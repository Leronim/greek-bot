import json
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


SENTENCES_PATH = Path("data/sentences_a1.json")


@dataclass(frozen=True)
class Sentence:
    id: str
    topic: str
    greek: str
    transcription: str
    ru: str
    note: str = ""


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
