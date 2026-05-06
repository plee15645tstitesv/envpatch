"""HMAC-based signing and verification for .env file integrity."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envpatch.parser import EnvFile

_ALGORITHM = "sha256"
_PREFIX = "hmac-sha256:"


@dataclass
class SignatureEntry:
    key: str
    digest: str  # hex digest of the value

    def as_dict(self) -> Dict[str, str]:
        return {"key": self.key, "digest": self.digest}


@dataclass
class SignatureManifest:
    entries: List[SignatureEntry] = field(default_factory=list)
    file_digest: str = ""  # digest over all (key, value) pairs in sorted order

    def as_dict(self) -> dict:
        return {
            "algorithm": _ALGORITHM,
            "file_digest": self.file_digest,
            "entries": [e.as_dict() for e in self.entries],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)

    @staticmethod
    def from_json(raw: str) -> "SignatureManifest":
        data = json.loads(raw)
        entries = [
            SignatureEntry(key=e["key"], digest=e["digest"])
            for e in data.get("entries", [])
        ]
        return SignatureManifest(entries=entries, file_digest=data.get("file_digest", ""))


def _hmac(secret: bytes, message: str) -> str:
    return hmac.new(secret, message.encode(), hashlib.sha256).hexdigest()


def sign_file(env_file: EnvFile, secret: str) -> SignatureManifest:
    """Produce a SignatureManifest for *env_file* using *secret*."""
    secret_bytes = secret.encode()
    entries: List[SignatureEntry] = []
    pairs: List[str] = []

    for entry in env_file.entries:
        if entry.is_comment or entry.key is None:
            continue
        value = entry.value or ""
        digest = _hmac(secret_bytes, f"{entry.key}={value}")
        entries.append(SignatureEntry(key=entry.key, digest=digest))
        pairs.append(f"{entry.key}={value}")

    combined = "\n".join(sorted(pairs))
    file_digest = _hmac(secret_bytes, combined)
    return SignatureManifest(entries=entries, file_digest=file_digest)


@dataclass
class VerifyResult:
    ok: bool
    tampered_keys: List[str] = field(default_factory=list)
    missing_keys: List[str] = field(default_factory=list)
    file_digest_ok: bool = True
    error: Optional[str] = None


def verify_file(env_file: EnvFile, manifest: SignatureManifest, secret: str) -> VerifyResult:
    """Verify *env_file* against *manifest*. Returns a VerifyResult."""
    secret_bytes = secret.encode()
    current_map = {
        e.key: e.value or ""
        for e in env_file.entries
        if not e.is_comment and e.key is not None
    }
    manifest_map = {e.key: e.digest for e in manifest.entries}

    tampered: List[str] = []
    missing: List[str] = []

    for key, expected_digest in manifest_map.items():
        if key not in current_map:
            missing.append(key)
            continue
        actual_digest = _hmac(secret_bytes, f"{key}={current_map[key]}")
        if not hmac.compare_digest(actual_digest, expected_digest):
            tampered.append(key)

    pairs = [f"{k}={v}" for k, v in current_map.items()]
    combined = "\n".join(sorted(pairs))
    file_digest = _hmac(secret_bytes, combined)
    file_digest_ok = hmac.compare_digest(file_digest, manifest.file_digest)

    all_ok = not tampered and not missing and file_digest_ok
    return VerifyResult(
        ok=all_ok,
        tampered_keys=tampered,
        missing_keys=missing,
        file_digest_ok=file_digest_ok,
    )
