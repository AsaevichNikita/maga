import re
import difflib
from typing import Iterable, List


# QWERTY <-> ЙЦУКЕН mapping (ошибка раскладки)
_EN = r"""`1234567890-=qwertyuiop[]\asdfghjkl;'zxcvbnm,./"""
_RU = r"""ё1234567890-=йцукенгшщзхъ\фывапролджэячсмитьбю."""

EN_TO_RU = {e: r for e, r in zip(_EN, _RU)}
RU_TO_EN = {r: e for e, r in zip(_EN, _RU)}

# uppercase
EN_TO_RU.update({k.upper(): v.upper() for k, v in list(EN_TO_RU.items())})
RU_TO_EN.update({k.upper(): v.upper() for k, v in list(RU_TO_EN.items())})


def swap_layout(text: str, direction: str) -> str:
    """
    direction:
      - 'en->ru'
      - 'ru->en'
    """
    if direction == "en->ru":
        mapping = EN_TO_RU
    elif direction == "ru->en":
        mapping = RU_TO_EN
    else:
        return text

    return "".join(mapping.get(ch, ch) for ch in text)


def normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("ё", "е")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s\-\/\.:@+]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_query_variants(q: str) -> List[str]:
    q = (q or "").strip()

    variants = [
        q,
        swap_layout(q, "en->ru"),
        swap_layout(q, "ru->en"),
    ]

    out = []
    seen = set()

    for variant in variants:
        normalized_variant = normalize(variant)
        if normalized_variant and normalized_variant not in seen:
            seen.add(normalized_variant)
            out.append(normalized_variant)

    return out


def similarity(query: str, text: str) -> float:
    """
    Эвристика сравнения:
    1. exact match
    2. query как подстрока
    3. query как префикс слова
    4. fuzzy fallback через difflib
    """
    if not query or not text:
        return 0.0

    query = normalize(query)
    text = normalize(text)

    if not query or not text:
        return 0.0

    if query == text:
        return 1.0

    if query in text:
        return 0.98

    text_tokens = text.split()
    query_tokens = query.split()

    for token in text_tokens:
        if token.startswith(query):
            return 0.95

    for q_token in query_tokens:
        for t_token in text_tokens:
            if t_token.startswith(q_token):
                return 0.92

    for token in text_tokens:
        if query in token:
            return 0.88

    full_ratio = difflib.SequenceMatcher(None, query, text).ratio()

    best_token_ratio = 0.0
    for q_token in (query_tokens or [query]):
        for t_token in (text_tokens or [text]):
            best_token_ratio = max(
                best_token_ratio,
                difflib.SequenceMatcher(None, q_token, t_token).ratio()
            )

    return 0.55 * full_ratio + 0.45 * best_token_ratio


def rank(items: Iterable, variants: List[str], label_fn, min_score: float = 0.20):
    scored = []

    for item in items:
        label = normalize(label_fn(item))
        if not label:
            continue

        score = 0.0
        for variant in variants:
            score = max(score, similarity(variant, label))

        if score >= min_score:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]