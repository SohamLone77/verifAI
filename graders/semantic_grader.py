# COST_TRACKING
from __future__ import annotations

from functools import lru_cache
from typing import Optional

import numpy as np

from app.models import Rubric
from graders import GraderResult, register_grader
from reward.cost_tracker import CostTracker


import os
from openai import OpenAI

def _get_client() -> OpenAI:
    """Lazily instantiate the OpenAI client."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None  # Fallback gracefully if not set
    return OpenAI(api_key=key)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors."""
    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


@register_grader("semantic")
class SemanticGrader:
    """
    Embedding-based grader.

    Computes cosine similarity between the agent's output and a gold-standard
    reference using sentence-transformers (all-MiniLM-L6-v2).

    When no gold standard is available, scores against the original prompt
    as a loose relevance signal.
    """

    def grade(
        self,
        prompt: str,
        output: str,
        rubric: Optional[Rubric] = None,
        reference: Optional[str] = None,
        cost_tracker: Optional[CostTracker] = None,
    ) -> GraderResult:
        client = _get_client()
        anchor = reference if reference else prompt

        usage_metadata = {}
        
        if client:
            # Native OpenAI Embeddings for tracking
            resp = client.embeddings.create(
                input=[anchor, output],
                model="text-embedding-3-small",
            )
            anchor_emb = resp.data[0].embedding
            output_emb = resp.data[1].embedding
            
            # Pass usage back out to be tracked
            usage_metadata = {
                "model": "text-embedding-3-small",
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.total_tokens - resp.usage.prompt_tokens,  # 0 for embeddings usually
            }
            if cost_tracker is not None:
                cost_tracker.track(
                    model=usage_metadata["model"],
                    prompt_tokens=usage_metadata["prompt_tokens"],
                    completion_tokens=usage_metadata["completion_tokens"],
                )
                usage_metadata["tracked"] = True
        else:
            # Fallback to local if no API key is set
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            emb = model.encode([anchor, output])
            anchor_emb = emb[0].tolist()
            output_emb = emb[1].tolist()

        sim = _cosine_similarity(anchor_emb, output_emb)

        # Map cosine sim [-1, 1] → [0, 1] (in practice most will be [0, 1])
        score = max(0.0, min(1.0, (sim + 1.0) / 2.0))

        return GraderResult(
            score=round(score, 4),
            breakdown={"semantic_similarity": round(sim, 4)},
            notes=[f"Cosine similarity to {'reference' if reference else 'prompt'}: {sim:.4f}"],
            metadata={"usage": usage_metadata} if usage_metadata else {}
        )
