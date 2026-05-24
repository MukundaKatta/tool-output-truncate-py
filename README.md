# tool-output-truncate-py

[![PyPI](https://img.shields.io/pypi/v/tool-output-truncate-py.svg)](https://pypi.org/project/tool-output-truncate-py/)
[![Python](https://img.shields.io/pypi/pyversions/tool-output-truncate-py.svg)](https://pypi.org/project/tool-output-truncate-py/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Truncate tool output before adding it to LLM message history.**

When an agent runs `cat file.log`, `ripgrep`, or a database query, the
result can be megabytes. Naively appending it to the conversation blows
the context window. The standard fix is to keep the head and the tail
and replace the middle with an elision marker. This is that, char-aware
(UTF-8 safe) and line-aware, with zero runtime dependencies.

Sibling to the Rust crate
[`tool-output-truncate`](https://crates.io/crates/tool-output-truncate).

## Install

```bash
pip install tool-output-truncate-py
```

## Use

```python
from tool_output_truncate import truncate_middle

big = open("server.log").read()
safe_to_send = truncate_middle(big, 4000)
# "first 2000 chars\n\n[123456 chars truncated]\n\n...last 2000 chars"
```

Four strategies:

```python
from tool_output_truncate import (
    truncate_head,
    truncate_tail,
    truncate_middle,
    truncate_middle_lines,
)

truncate_head(text, max_chars)         # keep prefix
truncate_tail(text, max_chars)         # keep suffix
truncate_middle(text, max_chars)       # keep both ends (default for logs)
truncate_middle_lines(text, max_lines) # line-aware version of middle
```

All four are no-ops when the input already fits.

### Examples

Keep the prefix (use when the tail is noise, e.g. long lists where
order matters):

```python
truncate_head("abcdefghij", 4)
# 'abcd\n\n[6 chars truncated]\n\n'
```

Keep the suffix (use when the head is preamble, e.g. command output
with banner lines):

```python
truncate_tail("abcdefghij", 4)
# '\n\n[6 chars truncated]\n\nghij'
```

Keep both ends (best default for arbitrary text where head and tail
both carry signal):

```python
truncate_middle("0123456789", 4)
# '01\n\n[6 chars truncated]\n\n89'
```

Line-aware middle (splits at line boundaries so you do not see half a
line of JSON or a partial stack-trace frame):

```python
text = "\n".join(f"line {i}" for i in range(100))
truncate_middle_lines(text, 4)
# 'line 0\nline 1\n[96 lines / ... chars truncated]\nline 98\nline 99'
```

UTF-8 is handled correctly. Python `str` is a sequence of codepoints,
so slicing never splits a multi-byte character. Emoji, accented Latin,
and CJK all count as one character each:

```python
truncate_head("crab" + "\U0001f980" * 8, 6)
# keeps 6 codepoints from the start, marker reports remaining count
```

## What it does NOT do

- No tokenization. Pass a char cap. As a rough Anthropic and OpenAI
  proxy, treat `chars * 4 == tokens` (so 4000 chars is about 1k tokens).
- No structured truncation (JSON, YAML, XML). For JSON specifically,
  parse first and decide which fields to keep.
- No summarization. This is character arithmetic only.

## Why a focused library

Most agent frameworks ship a custom truncator inline. They reinvent the
edge cases each time: UTF-8 boundaries, odd-sized budgets, line-aware
splitting that does not show half a line. This is the four-function
library you grab instead.

## License

MIT
