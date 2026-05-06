"""Formatting helpers for sign/verify output."""
from __future__ import annotations

from envpatch.sign import SignatureManifest, VerifyResult

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


def _c(text: str, code: str, colour: bool) -> str:
    return f"{code}{text}{_RESET}" if colour else text


def format_sign_saved(path: str, manifest: SignatureManifest, *, colour: bool = False) -> str:
    """One-line confirmation that a manifest was written."""
    count = len(manifest.entries)
    noun = "key" if count == 1 else "keys"
    label = _c("Manifest saved", _BOLD, colour)
    loc = _c(path, _YELLOW, colour)
    return f"{label}: {loc} ({count} {noun} signed)"


def format_verify_result(result: VerifyResult, *, colour: bool = False) -> str:
    """Human-readable summary of a VerifyResult."""
    lines: list[str] = []

    if result.ok:
        lines.append(_c("✓ Signature valid — file integrity confirmed.", _GREEN, colour))
        return "\n".join(lines)

    lines.append(_c("✗ Signature verification FAILED.", _RED, colour))

    if result.tampered_keys:
        header = _c("  Tampered keys:", _RED, colour)
        lines.append(header)
        for k in result.tampered_keys:
            lines.append(f"    - {k}")

    if result.missing_keys:
        header = _c("  Missing keys (removed since signing):", _YELLOW, colour)
        lines.append(header)
        for k in result.missing_keys:
            lines.append(f"    - {k}")

    if not result.file_digest_ok:
        lines.append(_c("  File-level digest mismatch (keys may have been added).", _RED, colour))

    if result.error:
        lines.append(_c(f"  Error: {result.error}", _RED, colour))

    return "\n".join(lines)
