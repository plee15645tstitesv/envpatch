# envpatch

> Lightweight utility to diff and merge `.env` files across environments without leaking secrets.

---

## Installation

```bash
pip install envpatch
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envpatch
```

---

## Usage

**Diff two `.env` files** — shows missing or changed keys without exposing values:

```bash
envpatch diff .env.example .env
```

**Merge a patch file into your local `.env`:**

```bash
envpatch merge .env.patch .env
```

**Generate a patch** (redacts secret values, keeps structure):

```bash
envpatch generate .env --output .env.patch
```

### Python API

```python
from envpatch import diff, merge

changes = diff(".env.example", ".env")
for key, status in changes.items():
    print(f"{key}: {status}")
```

---

## How It Works

- **Diff** compares keys across two `.env` files and reports `missing`, `added`, or `changed` — never printing secret values.
- **Merge** applies only the keys from a patch file, leaving untouched keys intact.
- **Generate** creates a shareable patch with values redacted by default.

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any significant changes.

---

## License

[MIT](LICENSE)