"""Formatting helpers for scope results."""
from __future__ import annotations

from envpatch.scope import ScopeResult

ANSI_CYAN = "\033[36m"
ANSI_YELLOW = "\033[33m"
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"


def _c(text: str, code: str, colour: bool) -> str:
    return f"{code}{text}{ANSI_RESET}" if colour else text


def format_scope_header(result: ScopeResult, colour: bool = False) -> str:
    prefix = _c(result.prefix, ANSI_BOLD, colour)
    count = _c(str(len(result.matched)), ANSI_CYAN, colour)
    return f"Scope '{prefix}': {count} matching key(s)"


def format_scope_summary(result: ScopeResult, colour: bool = False) -> str:
    lines = [format_scope_header(result, colour=colour)]
    if not result.ok():
        lines.append(_c("  (no keys matched)", ANSI_YELLOW, colour))
        return "\n".join(lines)
    for entry in result.matched:
        key = _c(entry.key or "", ANSI_CYAN, colour)
        value = entry.value if entry.value is not None else ""
        lines.append(f"  {key}={value}")
    return "\n".join(lines)


def format_scope_not_found(prefix: str, colour: bool = False) -> str:
    label = _c(prefix, ANSI_YELLOW, colour)
    return f"No keys found for scope '{label}'."
