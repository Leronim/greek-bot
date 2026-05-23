from pathlib import Path
from urllib.parse import urlencode

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import async_session_factory, create_db_schema
from app.models import Topic, User, Word, WordAnswer, WordExample
from app.repositories.words_repo import get_or_create_topic
from app.services.stats_service import admin_daily_activity
from app.utils.normalize import normalize_greek, normalize_russian

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app = FastAPI(title="Greek Bot Admin")


@app.on_event("startup")
async def startup() -> None:
    await create_db_schema()


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


def require_admin(request: Request) -> None:
    if request.cookies.get("admin_auth") != settings.admin_web_password:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})


def redirect(path: str, **params: str | int) -> RedirectResponse:
    query = f"?{urlencode(params)}" if params else ""
    return RedirectResponse(f"{path}{query}", status_code=status.HTTP_303_SEE_OTHER)


def split_answers(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def join_answers(answers: list[WordAnswer], direction: str) -> str:
    return " | ".join(answer.answer for answer in answers if answer.direction == direction)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(password: str = Form(...)) -> RedirectResponse:
    if password != settings.admin_web_password:
        return redirect("/login", error="wrong")
    response = redirect("/")
    response.set_cookie("admin_auth", password, httponly=True, samesite="lax")
    return response


@app.post("/logout")
async def logout() -> RedirectResponse:
    response = redirect("/login")
    response.delete_cookie("admin_auth")
    return response


@app.get("/", response_class=HTMLResponse)
async def words_list(
    request: Request,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    q: str = Query(default=""),
    topic: str = Query(default=""),
    page: int = Query(default=1, ge=1),
) -> HTMLResponse:
    per_page = 50
    query = (
        select(Word)
        .options(selectinload(Word.topic), selectinload(Word.answers))
        .join(Topic, Topic.id == Word.topic_id)
        .where(Word.level == "A1")
        .order_by(Topic.title.asc(), Word.greek.asc())
    )
    count_query = select(func.count(Word.id)).join(Topic, Topic.id == Word.topic_id).where(Word.level == "A1")

    if q:
        pattern = f"%{q}%"
        condition = or_(Word.greek.ilike(pattern), Word.ru.ilike(pattern), Word.slug.ilike(pattern))
        query = query.where(condition)
        count_query = count_query.where(condition)
    if topic:
        query = query.where(Topic.title == topic)
        count_query = count_query.where(Topic.title == topic)

    total = await session.scalar(count_query) or 0
    result = await session.execute(query.offset((page - 1) * per_page).limit(per_page))
    words = result.scalars().all()
    topics = await session.execute(select(Topic.title).where(Topic.level == "A1").order_by(Topic.title.asc()))

    return templates.TemplateResponse(
        "words.html",
        {
            "request": request,
            "words": words,
            "q": q,
            "topic": topic,
            "topics": topics.scalars().all(),
            "page": page,
            "pages": max(1, (total + per_page - 1) // per_page),
            "total": total,
        },
    )


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(
    request: Request,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    total_users = await session.scalar(select(func.count(User.id))) or 0
    total_words = await session.scalar(select(func.count(Word.id)).where(Word.is_active.is_(True))) or 0
    activity = await admin_daily_activity(session, limit=30)
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "total_users": total_users,
            "total_words": total_words,
            "activity": activity,
        },
    )


@app.get("/words/new", response_class=HTMLResponse)
async def new_word_page(request: Request, _: None = Depends(require_admin)) -> HTMLResponse:
    return templates.TemplateResponse("word_form.html", {"request": request, "word": None, "answers_el": "", "answers_ru": ""})


@app.get("/words/{word_id}", response_class=HTMLResponse)
async def edit_word_page(
    word_id: int,
    request: Request,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    word = await load_word(session, word_id)
    return templates.TemplateResponse(
        "word_form.html",
        {
            "request": request,
            "word": word,
            "answers_el": join_answers(word.answers, "ru_to_el"),
            "answers_ru": join_answers(word.answers, "el_to_ru"),
            "example": word.examples[0] if word.examples else None,
        },
    )


@app.post("/words")
async def create_word(
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    slug: str = Form(...),
    topic: str = Form(...),
    greek: str = Form(...),
    transcription: str = Form(default=""),
    ru: str = Form(...),
    part_of_speech: str = Form(default=""),
    gender: str = Form(default=""),
    greek_answers: str = Form(default=""),
    ru_answers: str = Form(default=""),
    example_el: str = Form(default=""),
    example_ru: str = Form(default=""),
    is_active: bool = Form(default=False),
) -> RedirectResponse:
    topic_obj = await get_or_create_topic(session, "A1", topic.strip())
    word = Word(
        slug=slug.strip(),
        level="A1",
        topic_id=topic_obj.id,
        greek=greek.strip(),
        transcription=transcription.strip() or None,
        ru=ru.strip(),
        part_of_speech=part_of_speech.strip() or None,
        gender=gender.strip() or None,
        is_active=is_active,
    )
    session.add(word)
    await session.flush()
    await replace_word_details(session, word, greek_answers, ru_answers, example_el, example_ru)
    await session.commit()
    return redirect("/words/" + str(word.id), saved=1)


@app.post("/words/{word_id}")
async def update_word(
    word_id: int,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    slug: str = Form(...),
    topic: str = Form(...),
    greek: str = Form(...),
    transcription: str = Form(default=""),
    ru: str = Form(...),
    part_of_speech: str = Form(default=""),
    gender: str = Form(default=""),
    greek_answers: str = Form(default=""),
    ru_answers: str = Form(default=""),
    example_el: str = Form(default=""),
    example_ru: str = Form(default=""),
    is_active: bool = Form(default=False),
) -> RedirectResponse:
    word = await load_word(session, word_id)
    topic_obj = await get_or_create_topic(session, "A1", topic.strip())
    word.slug = slug.strip()
    word.topic_id = topic_obj.id
    word.greek = greek.strip()
    word.transcription = transcription.strip() or None
    word.ru = ru.strip()
    word.part_of_speech = part_of_speech.strip() or None
    word.gender = gender.strip() or None
    word.is_active = is_active
    await replace_word_details(session, word, greek_answers, ru_answers, example_el, example_ru)
    await session.commit()
    return redirect("/words/" + str(word.id), saved=1)


@app.post("/words/{word_id}/delete")
async def delete_word(
    word_id: int,
    _: None = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    word = await load_word(session, word_id)
    await session.delete(word)
    await session.commit()
    return redirect("/")


async def load_word(session: AsyncSession, word_id: int) -> Word:
    result = await session.execute(
        select(Word)
        .options(selectinload(Word.topic), selectinload(Word.answers), selectinload(Word.examples))
        .where(Word.id == word_id)
    )
    word = result.scalar_one_or_none()
    if word is None:
        raise HTTPException(status_code=404)
    return word


async def replace_word_details(
    session: AsyncSession,
    word: Word,
    greek_answers: str,
    ru_answers: str,
    example_el: str,
    example_ru: str,
) -> None:
    await session.execute(delete(WordAnswer).where(WordAnswer.word_id == word.id))
    await session.execute(delete(WordExample).where(WordExample.word_id == word.id))
    await session.flush()

    greek_values = [word.greek, *split_answers(greek_answers)]
    ru_values = [word.ru, *split_answers(ru_answers)]
    for answer, normalized in unique_answers(greek_values, normalize_greek):
        session.add(WordAnswer(word_id=word.id, direction="ru_to_el", answer=answer, normalized_answer=normalized))
    for answer, normalized in unique_answers(ru_values, normalize_russian):
        session.add(WordAnswer(word_id=word.id, direction="el_to_ru", answer=answer, normalized_answer=normalized))

    if example_el.strip() and example_ru.strip():
        session.add(
            WordExample(
                word_id=word.id,
                example_el=example_el.strip(),
                example_ru=example_ru.strip(),
                sort_order=0,
            )
        )


def unique_answers(values: list[str], normalize) -> list[tuple[str, str]]:
    result: dict[str, str] = {}
    for value in values:
        value = value.strip()
        normalized = normalize(value)
        if value and normalized and normalized not in result:
            result[normalized] = value
    return [(answer, normalized) for normalized, answer in result.items()]
