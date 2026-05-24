"""Char-aware and line-aware truncation strategies for LLM tool output.

All four strategies are no-ops when the input already fits the requested
budget. UTF-8 safety is implicit: Python `str` is a sequence of Unicode
codepoints, so plain slicing never splits a multi-byte char. Length is
measured in codepoints (what `len(str)` returns), not bytes.
"""

from __future__ import annotations


def _char_elision(omitted: int) -> str:
    """Marker shown in place of removed text in the char-based strategies."""
    return f"\n\n[{omitted} chars truncated]\n\n"


def _line_elision(omitted_lines: int, omitted_chars: int) -> str:
    """Marker shown in place of removed lines in the line-based strategy."""
    return f"\n[{omitted_lines} lines / {omitted_chars} chars truncated]\n"


def _check_max(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be >= 0")


def truncate_head(s: str, max_chars: int) -> str:
    """Keep up to ``max_chars`` characters from the start.

    Everything after the cut is replaced with an elision marker that
    reports the count of omitted characters. Returns the input unchanged
    if it already fits.
    """
    _check_max("max_chars", max_chars)
    total = len(s)
    if total <= max_chars:
        return s
    omitted = total - max_chars
    return s[:max_chars] + _char_elision(omitted)


def truncate_tail(s: str, max_chars: int) -> str:
    """Keep up to ``max_chars`` characters from the end.

    Everything before the cut is replaced with an elision marker that
    reports the count of omitted characters. Returns the input unchanged
    if it already fits.
    """
    _check_max("max_chars", max_chars)
    total = len(s)
    if total <= max_chars:
        return s
    omitted = total - max_chars
    if max_chars == 0:
        return _char_elision(omitted)
    return _char_elision(omitted) + s[-max_chars:]


def truncate_middle(s: str, max_chars: int) -> str:
    """Keep up to ``max_chars`` characters by taking half from the start
    and half from the end, replacing the middle with an elision marker.

    ``max_chars`` is the budget for retained text only; the marker itself
    adds about 30 chars of overhead. With an odd budget, the tail gets
    one more char than the head. Returns the input unchanged if it
    already fits.
    """
    _check_max("max_chars", max_chars)
    total = len(s)
    if total <= max_chars:
        return s
    head = max_chars // 2
    tail = max_chars - head
    omitted = total - head - tail
    head_part = s[:head]
    # avoid s[-0:] which returns the whole string
    tail_part = s[-tail:] if tail > 0 else ""
    return head_part + _char_elision(omitted) + tail_part


def truncate_middle_lines(s: str, max_lines: int) -> str:
    """Keep up to ``max_lines`` lines by taking half from the start and
    half from the end, replacing the middle with an elision marker that
    reports omitted line count and omitted char count.

    Splits at ``\\n`` boundaries so callers do not see half a line of
    JSON or a partial stack-trace frame. With an odd budget, the tail
    gets one more line than the head. Returns the input unchanged if it
    already fits.

    Note: ``"a\\nb"`` splits into 2 entries and ``"a\\nb\\n"`` splits
    into 3 (the trailing empty entry after the final newline counts).
    """
    _check_max("max_lines", max_lines)
    lines = s.split("\n")
    total = len(lines)
    if total <= max_lines:
        return s
    head = max_lines // 2
    tail = max_lines - head
    omitted_lines = total - head - tail
    head_part = "\n".join(lines[:head])
    tail_part = "\n".join(lines[total - tail :]) if tail > 0 else ""
    # +1 per line for the surrounding newline; subtract 1 because the very
    # last omitted line does not contribute an extra trailing newline.
    omitted_chars = sum(len(line) + 1 for line in lines[head : total - tail])
    omitted_chars = max(omitted_chars - 1, 0)
    return head_part + _line_elision(omitted_lines, omitted_chars) + tail_part
