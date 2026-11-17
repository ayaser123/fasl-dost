"""Tiny local retrieval over curated guidance docs (markdown + frontmatter)."""
import math, re
from collections import Counter
from pathlib import Path

DIR = Path(__file__).parent / "knowledge"
_tok = lambda s: re.findall(r"[\w\u0600-\u06FF]+", s.lower())


def _load():
    docs = []
    for p in sorted(DIR.glob("*.md")):
        raw = p.read_text(encoding="utf-8")
        _, fm, body = raw.split("---", 2)
        meta = dict(l.split(":", 1) for l in fm.strip().splitlines() if ":" in l)
        meta = {k.strip(): v.strip() for k, v in meta.items()}
        text = f"{meta.get('title','')} {meta.get('keywords','')} {body}"
        docs.append({**meta, "body": body.strip(), "tokens": Counter(_tok(text))})
    return docs


DOCS = _load()
_df = Counter(t for d in DOCS for t in d["tokens"])


def search(query: str, crop: str | None = None, k: int = 4):
    q = _tok(query)
    out = []
    for d in DOCS:
        if crop and d["crop"] not in (crop.lower(), "general"):
            continue
        score = sum(
            (1 + math.log(d["tokens"][t])) * math.log(1 + len(DOCS) / _df[t])
            for t in q if d["tokens"][t]
        )
        if score > 0:
            out.append((score, d))
    out.sort(key=lambda x: -x[0])
    return [
        {"id": d["id"], "title": d["title"], "source": d["source"],
         "status": d["status"], "text": d["body"]}
        for _, d in out[:k]
    ]
