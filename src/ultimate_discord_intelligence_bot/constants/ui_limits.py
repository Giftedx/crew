"""UI display constants for Discord embeds and messages.

Centralizes truncation lengths and list limits to keep rendering consistent
across commands and easy to tweak.
"""

from __future__ import annotations

# URL and title truncation
MAX_URL_DISPLAY_LENGTH = 50
MAX_TITLE_DISPLAY_LENGTH = 100

# Keywords section
MAX_KEYWORDS_COUNT_DISPLAY = 8
MAX_KEYWORD_TEXT_LENGTH = 100

# Summary / perspective section
MAX_SUMMARY_DISPLAY_LENGTH = 300
