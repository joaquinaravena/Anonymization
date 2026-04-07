"""
Build recipient-oriented identity from the message only (To/Cc headers and greeting lines).

Used to scope anonymization to user-related spans. Account/phone tails are not inferred
from the body (phishing lure text is not treated as verified PII).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from config import USER_ONLY_MIN_NAME_TOKEN_LEN

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# To / Cc (EN) and À (FR) etc. — line-based header keys we treat as recipient-bearing.
_HEADER_KEY_RE = re.compile(
    r"^(?P<key>to|cc|bcc|à|pour)\s*:\s*(?P<value>.*)$",
    re.IGNORECASE,
)

# "Name <email@x.com>" or quoted display names
_DISPLAY_EMAIL_RE = re.compile(
    r"^(?P<name>[^<]+?)?\s*<(?P<email>[^>]+)>\s*$",
    re.IGNORECASE,
)

_GREETING_RES = (
    re.compile(r"^(?:Dear|Hi|Hello)\s+([^\n,]+?)(?:,|\s*$)", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^(?:Chère|Cher)\s+([^\n,]+?)(?:,|\s*$)", re.IGNORECASE | re.MULTILINE),
)


def _normalize_email(s: str) -> str:
    return s.strip().lower()


def extract_emails(s: str) -> list[str]:
    return _EMAIL_RE.findall(s)


def _normalize_name_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _name_tokens(name: str, min_len: int) -> set[str]:
    n = _normalize_name_text(name)
    if not n:
        return set()
    parts = [p for p in n.split() if len(p) >= min_len]
    out = set(parts)
    if len(n) >= min_len:
        out.add(n)
    return out


def _merge_alias_sets(*parts: str, min_len: int = USER_ONLY_MIN_NAME_TOKEN_LEN) -> frozenset[str]:
    acc: set[str] = set()
    for p in parts:
        if not p:
            continue
        acc |= _name_tokens(p, min_len)
    return frozenset(acc)


@dataclass(frozen=True)
class UserIdentity:
    emails: frozenset[str]
    email_local_parts: frozenset[str]
    name_aliases: frozenset[str]
    to_cc_line_ranges: tuple[tuple[int, int], ...]
    body_start: int

    def is_empty(self) -> bool:
        return not self.emails and not self.name_aliases

    def span_in_to_cc_line(self, start: int, end: int) -> bool:
        for a, b in self.to_cc_line_ranges:
            if start >= a and end <= b:
                return True
        return False


def _find_header_body_split(text: str) -> tuple[str, int]:
    idx = text.find("\n\n")
    if idx == -1:
        return text, len(text)
    return text[:idx], idx + 2


_TO_CC_LINE_IN_HEAD = re.compile(
    r"(?im)^(?:to|cc|bcc|à|pour)\s*:\s*.*$",
)


def _collect_to_cc_ranges_in_header_prefix(text: str, body_start: int) -> tuple[tuple[int, int], ...]:
    head = text[:body_start]
    return tuple((m.start(), m.end()) for m in _TO_CC_LINE_IN_HEAD.finditer(head))


def _extract_emails_and_names_from_header_value(value: str) -> tuple[set[str], set[str]]:
    emails: set[str] = set()
    names: set[str] = set()
    value = value.strip()
    dm = _DISPLAY_EMAIL_RE.match(value)
    if dm:
        em = dm.group("email")
        nm = dm.group("name")
        if em:
            emails.add(_normalize_email(em))
        if nm:
            names.add(nm.strip().strip('"').strip("'"))
        return emails, names
    for em in _EMAIL_RE.findall(value):
        emails.add(_normalize_email(em))
    return emails, names


def _greeting_names(body: str) -> list[str]:
    found: list[str] = []
    for rx in _GREETING_RES:
        for m in rx.finditer(body):
            g = m.group(1).strip()
            if g:
                found.append(g)
    return found


def build_user_identity(
    text: str,
    *,
    min_token_len: int = USER_ONLY_MIN_NAME_TOKEN_LEN,
) -> UserIdentity:
    header_block, body_start = _find_header_body_split(text)
    body = text[body_start:]

    emails: set[str] = set()
    names: set[str] = set()

    for line in header_block.splitlines():
        stripped = line.strip()
        m = _HEADER_KEY_RE.match(stripped)
        if m:
            key = m.group("key").lower()
            if key in ("to", "cc", "bcc", "à", "pour"):
                value = m.group("value")
                ems, nms = _extract_emails_and_names_from_header_value(value)
                emails |= ems
                names |= nms

    for g in _greeting_names(body):
        names.add(g)

    name_aliases = _merge_alias_sets(*names, min_len=min_token_len)

    local_parts: set[str] = set()
    for e in emails:
        if "@" in e:
            local_parts.add(e.split("@", 1)[0].lower())

    to_cc_ranges = _collect_to_cc_ranges_in_header_prefix(text, body_start)

    return UserIdentity(
        emails=frozenset(emails),
        email_local_parts=frozenset(local_parts),
        name_aliases=name_aliases,
        to_cc_line_ranges=to_cc_ranges,
        body_start=body_start,
    )
