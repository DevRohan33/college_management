import numpy as np
from openai import OpenAI
from .models import dataChunks as KBChunk

client = OpenAI()

def embed_query(q: str):
    return client.embeddings.create(
        model="text-embedding-3-small",
        input=q
    ).data[0].embedding

def top_k_chunks(query: str, k: int = 4):
    qv = np.array(embed_query(query), dtype=np.float32)
    rows = KBChunk.objects.all().only("text","embedding","source")
    scored = []
    qnorm = np.linalg.norm(qv)
    for r in rows:
        dv = np.array(r.embedding, dtype=np.float32)
        score = float(np.dot(qv, dv) / (qnorm * (np.linalg.norm(dv) + 1e-10)))
        scored.append((score, r))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]

def build_context(query: str, k: int = 4, max_chars: int = 2000):
    chunks = top_k_chunks(query, k=k)
    ctx_parts, total = [], 0
    for score, row in chunks:
        part = f"[{row.source}] {row.text}\n"
        if total + len(part) > max_chars: break
        ctx_parts.append(part); total += len(part)
    return "\n".join(ctx_parts)
