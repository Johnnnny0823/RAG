"""Deterministic bilingual lexical baseline for Taiwanese patent text."""

import re
import unicodedata

TOKENIZER_VERSION = "han-bigram-v1"
HAN = r"\u3400-\u4dbf\u4e00-\u9fff\U00020000-\U000323af"
RUNS = re.compile(rf"[{HAN}]+|[a-z0-9]+")
MARKUP = re.compile(r"<br\s*/?>", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    text = MARKUP.sub(" ", unicodedata.normalize("NFKC", text).casefold())
    tokens = []
    for match in RUNS.finditer(text):
        run = match.group()
        if run.isascii():
            tokens.append("w" + run)
            continue
        if len(run) == 1:
            tokens.append(f"h{ord(run):06x}")
        else:
            tokens.extend(
                f"h{ord(left):06x}{ord(right):06x}" for left, right in zip(run, run[1:])
            )
    return tokens
