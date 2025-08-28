import numpy as np
from openai import OpenAI
from .models import dataChunks as KBChunk

client = OpenAI()

# ---- Embed Query ----
def embed_query(q: str, model="text-embedding-3-small"):
    """Return embedding vector for a query"""
    return client.embeddings.create(
        model=model,
        input=q
    ).data[0].embedding

# ---- Top K Retrieval ----
def top_k_chunks(query: str, k: int = 4):
    """Retrieve top-k most relevant chunks from DB"""
    qv = np.array(embed_query(query), dtype=np.float32)
    qv = qv / (np.linalg.norm(qv) + 1e-10)  # normalize

    rows = KBChunk.objects.all().only("text", "embedding", "source")
    scored = []
    for r in rows:
        dv = np.array(r.embedding, dtype=np.float32)
        dv = dv / (np.linalg.norm(dv) + 1e-10)
        score = float(np.dot(qv, dv))
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]


# ---- Build Context ----
def build_context(query: str, k: int = 4, max_chars: int = 2000):
    """Build context string from retrieved chunks"""
    chunks = top_k_chunks(query, k=k)
    ctx_parts, total = [], 0
    for score, row in chunks:
        part = f"Source: {row.source}\nText: {row.text}\n---\n"
        if total + len(part) > max_chars:
            break
        ctx_parts.append(part)
        total += len(part)

    return "\n".join(ctx_parts)
