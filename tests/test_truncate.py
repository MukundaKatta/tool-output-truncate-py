import pytest

from tool_output_truncate import (
    truncate_head,
    truncate_middle,
    truncate_middle_lines,
    truncate_tail,
)

# ---------- passthrough behavior ----------


def test_passthrough_when_under_cap():
    assert truncate_head("hello", 100) == "hello"
    assert truncate_tail("hello", 100) == "hello"
    assert truncate_middle("hello", 100) == "hello"


def test_passthrough_when_exactly_at_cap():
    assert truncate_head("hello", 5) == "hello"
    assert truncate_tail("hello", 5) == "hello"
    assert truncate_middle("hello", 5) == "hello"


def test_empty_input_passthrough():
    assert truncate_head("", 10) == ""
    assert truncate_tail("", 10) == ""
    assert truncate_middle("", 10) == ""
    assert truncate_middle_lines("", 10) == ""


# ---------- truncate_head ----------


def test_truncate_head_keeps_prefix():
    out = truncate_head("abcdefghij", 4)
    assert out.startswith("abcd")
    assert "6 chars truncated" in out


def test_truncate_head_omitted_count_is_accurate():
    s = "x" * 1000
    out = truncate_head(s, 100)
    assert out.startswith("x" * 100)
    assert "900 chars truncated" in out


def test_truncate_head_zero_max_keeps_nothing():
    out = truncate_head("hello world", 0)
    assert "hello" not in out
    assert "11 chars truncated" in out


# ---------- truncate_tail ----------


def test_truncate_tail_keeps_suffix():
    out = truncate_tail("abcdefghij", 4)
    assert out.endswith("ghij")
    assert "6 chars truncated" in out


def test_truncate_tail_omitted_count_is_accurate():
    s = "x" * 1000 + "TAIL"
    out = truncate_tail(s, 4)
    assert out.endswith("TAIL")
    assert "1000 chars truncated" in out


def test_truncate_tail_zero_max_keeps_nothing():
    out = truncate_tail("hello world", 0)
    assert "hello" not in out
    assert "11 chars truncated" in out


# ---------- truncate_middle ----------


def test_truncate_middle_keeps_both_ends():
    out = truncate_middle("abcdefghij", 4)
    assert out.startswith("ab")
    assert out.endswith("ij")
    assert "6 chars truncated" in out


def test_truncate_middle_odd_budget_gives_tail_one_more():
    # max=5 -> head=2, tail=3
    out = truncate_middle("0123456789", 5)
    assert out.startswith("01")
    assert out.endswith("789")
    assert "5 chars truncated" in out


def test_truncate_middle_one_char_budget_keeps_only_tail():
    # max=1 -> head=0, tail=1. head_part is "", tail_part is last char.
    out = truncate_middle("abcdefghij", 1)
    assert out.endswith("j")
    assert "9 chars truncated" in out


def test_truncate_middle_zero_budget_keeps_only_marker():
    # max=0 -> head=0, tail=0. Both ends empty, output is just the marker.
    out = truncate_middle("abcdef", 0)
    assert "abc" not in out
    assert out == _marker_for_chars(6)


# ---------- UTF-8 / multi-byte safety ----------


def test_emoji_is_not_split():
    # 8 crab emoji, each is one codepoint but multiple bytes in UTF-8
    crab = "\U0001f980"
    s = crab * 8
    out = truncate_head(s, 3)
    assert out.startswith(crab * 3)
    assert "5 chars truncated" in out
    # the result encodes cleanly
    assert out.encode("utf-8").decode("utf-8") == out


def test_accented_chars_count_as_one():
    # "naïve résumé café" has accents that are still one codepoint each
    s = "naïve résumé café"
    assert len(s) == 17
    out = truncate_head(s, 4)
    assert out.startswith("naïv")
    assert "13 chars truncated" in out


def test_cjk_chars_count_as_one_each():
    # Chinese: each char is 3 bytes in UTF-8 but one codepoint
    s = "你好世界你好世界"
    assert len(s) == 8
    out = truncate_middle(s, 4)
    assert out.startswith("你好")
    assert out.endswith("世界")
    assert "4 chars truncated" in out


def test_mixed_unicode_round_trip():
    s = "hello \U0001f30d café 世界 " * 50
    out = truncate_middle(s, 50)
    # length retained for text only (marker adds overhead)
    assert out.encode("utf-8").decode("utf-8") == out


# ---------- truncate_middle_lines ----------


def _lines_block(n: int) -> str:
    return "\n".join(f"line {i}" for i in range(n))


def test_lines_passthrough_under_cap():
    s = "a\nb\nc"
    assert truncate_middle_lines(s, 100) == s


def test_lines_single_line_input():
    s = "just one line, no newline"
    assert truncate_middle_lines(s, 5) == s
    assert truncate_middle_lines(s, 1) == s


def test_lines_keeps_head_and_tail():
    s = _lines_block(100)  # 100 entries (no trailing newline)
    out = truncate_middle_lines(s, 4)
    assert out.startswith("line 0\nline 1")
    assert out.endswith("line 98\nline 99")
    assert "lines /" in out
    assert "truncated" in out


def test_lines_marker_reports_omitted_line_count():
    s = _lines_block(20)
    out = truncate_middle_lines(s, 4)  # head=2, tail=2 -> 16 omitted
    assert "16 lines" in out


def test_lines_odd_max_splits_one_more_to_tail():
    s = _lines_block(20)
    out = truncate_middle_lines(s, 5)  # head=2, tail=3
    assert out.startswith("line 0\nline 1\n")
    assert out.endswith("line 17\nline 18\nline 19")


def test_lines_with_trailing_newline_counts_empty_tail_entry():
    # "a\nb\n" splits into 3 entries: ['a', 'b', '']
    s = "a\nb\nc\nd\ne\nf\n"  # 7 entries: 6 lines + 1 empty
    out = truncate_middle_lines(s, 2)
    # head=1 tail=1: head_part='a', tail_part=''
    assert out.startswith("a\n")
    assert "5 lines" in out


def test_lines_handles_unicode_lines():
    s = "café\n\U0001f30d\nhello\n世界\nfoo\nbar\nbaz"
    out = truncate_middle_lines(s, 2)
    # head=1 tail=1: head_part='café', tail_part='baz'
    assert out.startswith("café")
    assert out.endswith("baz")
    assert "5 lines" in out


def test_lines_omitted_char_count_matches_removed_middle():
    # 10 entries, head=2 tail=2 -> middle is lines[2:8] joined by "\n".
    s = _lines_block(10)
    out = truncate_middle_lines(s, 4)
    middle = "\n".join(f"line {i}" for i in range(2, 8))
    assert f"6 lines / {len(middle)} chars truncated" in out


def test_lines_one_line_budget_keeps_only_tail():
    # max=1 -> head=0, tail=1. head_part is "", tail_part is the last line.
    s = _lines_block(5)
    out = truncate_middle_lines(s, 1)
    assert out.endswith("line 4")
    assert "line 0" not in out
    assert "4 lines" in out


def test_lines_zero_budget_keeps_only_marker():
    # max=0 -> head=0, tail=0. Output is just the line marker.
    s = _lines_block(5)
    out = truncate_middle_lines(s, 0)
    assert "line 0" not in out
    assert "line 4" not in out
    assert "5 lines" in out


# ---------- validation ----------


def test_negative_max_chars_raises():
    with pytest.raises(ValueError):
        truncate_head("hi", -1)
    with pytest.raises(ValueError):
        truncate_tail("hi", -1)
    with pytest.raises(ValueError):
        truncate_middle("hi", -1)
    with pytest.raises(ValueError):
        truncate_middle_lines("hi\nho", -1)


# ---------- combined / large input ----------


def test_large_input_truncate_middle_is_within_budget():
    s = "x" * 100_000
    out = truncate_middle(s, 1000)
    # retained text = 1000, marker overhead is bounded
    assert "99000 chars truncated" in out
    text_only = out.replace(_marker_for_chars(99000), "")
    assert len(text_only) == 1000


def test_chained_truncators_idempotent_when_fits():
    s = "small input"
    out = truncate_head(truncate_tail(truncate_middle(s, 100), 100), 100)
    assert out == s


def _marker_for_chars(n: int) -> str:
    return f"\n\n[{n} chars truncated]\n\n"
