"""tool-output-truncate - truncate LLM tool output before it blows the context window.

Four char-aware and line-aware strategies, all no-ops when the input
already fits. UTF-8 safe (Python `str` is codepoints, so slicing never
splits multi-byte chars). Zero runtime dependencies.

    from tool_output_truncate import truncate_middle

    big = open("server.log").read()
    safe_to_send = truncate_middle(big, 4000)

Strategies:

  * ``truncate_head(s, max_chars)``         - keep the prefix.
  * ``truncate_tail(s, max_chars)``         - keep the suffix.
  * ``truncate_middle(s, max_chars)``       - keep both ends.
  * ``truncate_middle_lines(s, max_lines)`` - line-aware version of middle.

Sibling to the Rust crate `tool-output-truncate`.
"""

from tool_output_truncate.truncate import (
    truncate_head,
    truncate_middle,
    truncate_middle_lines,
    truncate_tail,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "truncate_head",
    "truncate_middle",
    "truncate_middle_lines",
    "truncate_tail",
]
