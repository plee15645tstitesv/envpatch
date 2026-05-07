"""Formatting helpers for chain results."""
from __future__ import annotations

from .chain import ChainResult


def _c(text: str, code: str, colour: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if colour else text


def format_chain_header(names: list[str], colour: bool = False) -> str:
    """Return a header line describing the chain order."""
    arrow = " -> "
    chain_str = arrow.join(
        _c(n, "36", colour) for n in names
    )
    label = _c("chain:", "1", colour)
    return f"{label} {chain_str}"


def format_chain_summary(result: ChainResult, colour: bool = False) -> str:
    """Return a one-line summary of the resolved chain."""
    total = result.total_keys()
    key_word = "key" if total == 1 else "keys"
    count_str = _c(str(total), "33", colour)
    return f"resolved {count_str} {key_word} across {len(result.chain_names)} file(s)"


def format_chain_source_map(
    result: ChainResult, colour: bool = False
) -> str:
    """Return a multi-line table of key -> source file."""
    if not result.source_map:
        return _c("(no keys)", "2", colour)

    lines = []
    for key, source in sorted(result.source_map.items()):
        key_str = _c(key, "32", colour)
        src_str = _c(source, "36", colour)
        lines.append(f"  {key_str}  <-  {src_str}")
    return "\n".join(lines)


def format_chain_report(result: ChainResult, colour: bool = False) -> str:
    """Return a full human-readable chain report."""
    parts = [
        format_chain_header(result.chain_names, colour),
        format_chain_summary(result, colour),
        format_chain_source_map(result, colour),
    ]
    return "\n".join(parts)
