"""
Semantic retrieval over the curated CPF housing knowledge base, using
OpenAI embeddings instead of word-overlap (TF-IDF) matching.

Why this matters: word-overlap matching only counts shared words between
a question and a knowledge base entry. It fails when someone phrases a
question differently than the source document -- e.g. "have I already
met my FRS" vs. the source's wording "have set aside their Full
Retirement Sum" share almost no words, even though they mean the same
thing. Embeddings convert text into a vector that represents its
*meaning*, so semantically similar text scores highly even with
completely different wording.

Embeddings for the knowledge base are computed once and cached to a
local file (data/kb_embeddings_cache.json), keyed by a hash of the
knowledge base content. If the knowledge base changes, the cache is
automatically invalidated and re-computed on the next run -- this keeps
costs and startup time down without needing a separate "rebuild cache"
step.
"""

import hashlib
import json
from pathlib import Path
from functools import lru_cache

import streamlit as st

from utils.openai_client import get_client

KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base.json"
CACHE_PATH = Path(__file__).parent.parent / "data" / "kb_embeddings_cache.json"
EMBEDDING_MODEL = "text-embedding-3-small"

# Minimum cosine similarity for a knowledge base entry to be considered a
# real match. Calibrated empirically using scripts/calibrate_retrieval.py
# against real on-topic questions (scored 0.514-0.682) and off-topic
# questions (scored at or below 0.489), which cleanly separated at 0.5.
# If the knowledge base grows significantly, re-run the calibration script
# and adjust this value if needed.
MIN_RELEVANCE_SCORE = 0.5


@lru_cache(maxsize=1)
def load_knowledge_base():
    """Load the knowledge base once and cache it for the app's lifetime."""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _kb_content_hash(kb) -> str:
    """Hash the knowledge base content so we know when the cache is stale."""
    joined = "||".join(f"{e['id']}:{e['content']}" for e in kb)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _embed(client, text: str) -> list[float]:
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@st.cache_resource(show_spinner="Preparing the knowledge base for search...")
def _build_index():
    """
    Compute (or load from cache) embeddings for every knowledge base entry.
    Cached for the lifetime of the Streamlit app process via
    st.cache_resource, and also persisted to disk so a fresh app restart
    doesn't need to re-call the embeddings API for unchanged content.
    """
    kb = load_knowledge_base()
    current_hash = _kb_content_hash(kb)

    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("hash") == current_hash:
                return kb, cached["embeddings"]
        except (json.JSONDecodeError, KeyError):
            pass  # fall through and rebuild

    client = get_client()
    embeddings = [_embed(client, f"{e['topic']}. {e['content']}") for e in kb]

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump({"hash": current_hash, "embeddings": embeddings}, f)

    return kb, embeddings


def retrieve(query: str, top_k: int = 3, min_score: float = MIN_RELEVANCE_SCORE):
    """
    Return the top_k most relevant knowledge base entries for a query,
    excluding matches below min_score, using semantic (embedding-based)
    similarity rather than keyword overlap.

    Each returned entry is a dict with topic, source_name, source_url,
    last_verified, and content -- everything needed to ground an LLM
    answer and show a citation to the user.
    """
    kb, kb_embeddings = _build_index()
    client = get_client()
    query_embedding = _embed(client, query)

    scored = [
        (i, _cosine_similarity(query_embedding, kb_embeddings[i]))
        for i in range(len(kb))
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    for i, score in scored[:top_k]:
        if score < min_score:
            continue
        entry = dict(kb[i])
        entry["relevance_score"] = round(score, 3)
        results.append(entry)
    return results
