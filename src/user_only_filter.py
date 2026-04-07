"""
Filter Presidio recognizer results to recipient-related spans only.
"""

from __future__ import annotations

from typing import Sequence

from presidio_analyzer import RecognizerResult
from rapidfuzz import fuzz

from config import USER_ONLY_FUZZY_MATCH_THRESHOLD
from user_identity import UserIdentity, extract_emails, _normalize_email


def _overlap(a: RecognizerResult, b: RecognizerResult) -> bool:
    return a.start < b.end and b.start < a.end


def resolve_overlaps(results: Sequence[RecognizerResult]) -> list[RecognizerResult]:
    """Drop overlapping spans: walk in order of (start, longest first, highest score), keep non-overlapping."""
    ordered = sorted(
        results,
        key=lambda r: (r.start, -(r.end - r.start), -r.score),
    )
    kept: list[RecognizerResult] = []
    for r in ordered:
        if any(_overlap(r, k) for k in kept):
            continue
        kept.append(r)
    return sorted(kept, key=lambda r: r.start)


def _span(text: str, r: RecognizerResult) -> str:
    return text[r.start : r.end]


def _email_in_set(span: str, identity: UserIdentity) -> bool:
    for em in extract_emails(span):
        if _normalize_email(em) in identity.emails:
            return True
    return False


def _url_has_user_identifier(span: str, identity: UserIdentity) -> bool:
    s = span.lower()
    for e in identity.emails:
        if e and e in s:
            return True
    for lp in identity.email_local_parts:
        if len(lp) >= 3 and lp in s:
            return True
    return False


def _person_matches(span: str, identity: UserIdentity, threshold: float) -> bool:
    if not identity.name_aliases:
        return False
    raw = span.strip()
    if not raw:
        return False
    for alias in identity.name_aliases:
        if not alias:
            continue
        if alias in raw.lower() or raw.lower() in alias:
            return True
        if fuzz.token_sort_ratio(raw, alias) >= threshold:
            return True
        if fuzz.partial_ratio(raw, alias) >= threshold:
            return True
    return False


def is_user_related(
    text: str,
    r: RecognizerResult,
    identity: UserIdentity,
    *,
    fuzzy_threshold: float = USER_ONLY_FUZZY_MATCH_THRESHOLD,
) -> bool:
    span = _span(text, r)
    et = r.entity_type

    if et == "EMAIL_ADDRESS":
        return _email_in_set(span, identity)

    if et == "URL":
        return _url_has_user_identifier(span, identity)

    if et == "PHONE_NUMBER":
        return False

    if et == "ACCOUNT_NUMBER":
        return False

    if et == "PERSON":
        if identity.span_in_to_cc_line(r.start, r.end):
            return True
        return _person_matches(span, identity, fuzzy_threshold)

    if et in ("ADDRESS", "LOCATION", "DATE_TIME", "CREDIT_CARD"):
        # Keep only if clearly inside recipient header line (rare)
        return identity.span_in_to_cc_line(r.start, r.end)

    return False


def filter_user_only_results(
    text: str,
    results: Sequence[RecognizerResult],
    identity: UserIdentity,
    *,
    fuzzy_threshold: float = USER_ONLY_FUZZY_MATCH_THRESHOLD,
) -> list[RecognizerResult]:
    kept = [
        r
        for r in results
        if is_user_related(text, r, identity, fuzzy_threshold=fuzzy_threshold)
    ]
    return resolve_overlaps(kept)
