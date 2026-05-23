import re
import unicodedata


_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_SPACES_RE = re.compile(r"\s+")


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def normalize_greek(value: str) -> str:
    value = strip_accents(value).lower().replace("ς", "σ")
    value = _PUNCT_RE.sub(" ", value)
    return _SPACES_RE.sub(" ", value).strip()


def normalize_russian(value: str) -> str:
    value = value.lower().replace("ё", "е")
    value = _PUNCT_RE.sub(" ", value)
    return _SPACES_RE.sub(" ", value).strip()


def normalize_answer(value: str, direction: str) -> str:
    if direction == "ru_to_el":
        return normalize_greek(value)
    return normalize_russian(value)
