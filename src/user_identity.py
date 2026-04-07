"""
Build recipient-oriented identity from structured email headers.

Identity is derived from parsed recipient headers (To/Cc/Bcc),
without relying on language-specific greeting words in the body.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses

from config import USER_ONLY_MIN_NAME_TOKEN_LEN

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
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
    first_line_name_used: bool

    def is_empty(self) -> bool:
        return not self.emails and not self.name_aliases

    def source(self) -> str:
        if self.first_line_name_used and self.emails:
            return "headers_plus_first_line"
        if self.first_line_name_used and not self.emails:
            return "first_line_only"
        if self.emails and self.name_aliases:
            return "headers_email_and_name"
        if self.emails:
            return "headers_email_only"
        if self.name_aliases:
            return "headers_name_only"
        return "none"

    def span_in_to_cc_line(self, start: int, end: int) -> bool:
        for a, b in self.to_cc_line_ranges:
            if start >= a and end <= b:
                return True
        return False


def _find_header_body_split(text: str) -> tuple[str, int]:
    for sep in ("\r\n\r\n", "\n\n", "\r\r"):
        idx = text.find(sep)
        if idx != -1:
            return text[:idx], idx + len(sep)
    return text, len(text)


_TO_CC_LINE_IN_HEAD = re.compile(r"(?im)^(?:to|cc|bcc)\s*:\s*.*$")


def _collect_to_cc_ranges_in_header_prefix(text: str, body_start: int) -> tuple[tuple[int, int], ...]:
    head = text[:body_start]
    return tuple((m.start(), m.end()) for m in _TO_CC_LINE_IN_HEAD.finditer(head))


def _parse_recipients_from_email_headers(text: str) -> tuple[set[str], set[str]]:
    """
    Parse RFC-compliant headers robustly (CRLF/folded lines/encoded names).
    """
    emails: set[str] = set()
    names: set[str] = set()
    try:
        msg = BytesParser(policy=policy.default).parsebytes(text.encode("utf-8", errors="ignore"))
    except Exception:
        return emails, names

    raw_values: list[str] = []
    for key in ("To", "Cc", "Bcc"):
        raw_values.extend(msg.get_all(key, []))

    for name, addr in getaddresses(raw_values):
        if addr:
            emails.add(_normalize_email(addr))
        if name and name.strip():
            names.add(name.strip())
    return emails, names


def _extract_first_line_name_candidate(text: str, body_start: int) -> str | None:
    """
    Language-neutral heuristic: inspect first non-empty body line and extract a name-like span.
    Intended to recover recipient names when headers contain only the email address.
    """
    body = text[body_start:]
    if not body:
        return None

    first_line = ""
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line:
            first_line = line
            break
    if not first_line:
        return None

    # Common non-name shapes in first lines.
    if "@" in first_line or "http://" in first_line.lower() or "https://" in first_line.lower():
        return None
    if ":" in first_line:
        return None
    if re.search(r"\d", first_line):
        return None

    candidate = first_line.split(",", 1)[0].strip().strip("-")
    tokens = re.findall(r"[^\W\d_]+", candidate, flags=re.UNICODE)
    if len(tokens) < 2:
        return None

    # Heuristic: if line has 3+ tokens, first token is often a salutation/title.
    if len(tokens) >= 3:
        tokens = tokens[1:]
    if len(tokens) < 2:
        return None

    normalized_tokens = [t for t in tokens if len(t) >= 2]
    if len(normalized_tokens) < 2:
        return None
    return " ".join(normalized_tokens[:4])


def build_user_identity(
    text: str,
    *,
    min_token_len: int = USER_ONLY_MIN_NAME_TOKEN_LEN,
) -> UserIdentity:
    _header_block, body_start = _find_header_body_split(text)

    emails: set[str] = set()
    names: set[str] = set()

    header_emails, header_names = _parse_recipients_from_email_headers(text)
    emails |= header_emails
    names |= header_names

    first_line_name_used = False
    first_line_candidate = _extract_first_line_name_candidate(text, body_start)
    if first_line_candidate:
        names.add(first_line_candidate)
        first_line_name_used = True

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
        first_line_name_used=first_line_name_used,
    )
