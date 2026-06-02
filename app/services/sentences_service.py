from difflib import SequenceMatcher
import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.utils.normalize import normalize_greek


SENTENCES_PATH = Path("data/sentences_a1.json")


@dataclass(frozen=True)
class Sentence:
    id: str
    topic: str
    greek: str
    transcription: str
    ru: str
    note: str = ""


@dataclass(frozen=True)
class SentenceAnswerCheck:
    status: str
    normalized_user_answer: str
    normalized_correct_answer: str

    @property
    def is_correct(self) -> bool:
        return self.status == "correct"

    @property
    def is_almost(self) -> bool:
        return self.status == "almost"


@lru_cache
def load_sentences() -> list[Sentence]:
    if not SENTENCES_PATH.exists():
        return []
    data = json.loads(SENTENCES_PATH.read_text(encoding="utf-8"))
    return [Sentence(**item) for item in data]


def get_sentence(index: int) -> Sentence | None:
    sentences = load_sentences()
    if not sentences:
        return None
    return sentences[index % len(sentences)]


def random_sentence_index() -> int | None:
    sentences = load_sentences()
    if not sentences:
        return None
    return random.randrange(len(sentences))


def next_sentence_index(index: int) -> int:
    sentences = load_sentences()
    if not sentences:
        return 0
    return (index + 1) % len(sentences)


def is_correct_sentence_answer(sentence: Sentence, answer: str) -> bool:
    return normalize_greek(answer) == normalize_greek(sentence.greek)


def check_sentence_answer(sentence: Sentence, answer: str) -> SentenceAnswerCheck:
    normalized_answer = normalize_greek(answer)
    normalized_correct = normalize_greek(sentence.greek)
    if normalized_answer == normalized_correct:
        return SentenceAnswerCheck("correct", normalized_answer, normalized_correct)
    if is_almost_sentence_answer(normalized_answer, normalized_correct):
        return SentenceAnswerCheck("almost", normalized_answer, normalized_correct)
    return SentenceAnswerCheck("wrong", normalized_answer, normalized_correct)


def is_almost_sentence_answer(normalized_answer: str, normalized_correct: str) -> bool:
    if not normalized_answer or not normalized_correct:
        return False

    answer_words = normalized_answer.split()
    correct_words = normalized_correct.split()
    word_count = len(correct_words)
    distance = levenshtein_distance(normalized_answer, normalized_correct)

    if word_count <= 2:
        return distance <= 1
    if word_count <= 5:
        return distance <= 2 or SequenceMatcher(None, normalized_answer, normalized_correct).ratio() >= 0.9
    allowed_distance = max(2, round(len(normalized_correct) * 0.15))
    return distance <= allowed_distance or SequenceMatcher(None, normalized_answer, normalized_correct).ratio() >= 0.86


def levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            insert_cost = current[right_index - 1] + 1
            delete_cost = previous[right_index] + 1
            replace_cost = previous[right_index - 1] + (left_char != right_char)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]
