"""
Reference material store for retrieval-augmented grading.

Two kinds of material can be attached to a question bank:
- an answer key, split by question number and matched to each question directly
- course material (notes, textbook chapters), split into chunks and searched per question

Chunks are embedded with EMBEDDING_MODEL through LiteLLM and stored in the
vector_store table. When embeddings are unavailable (no key, EMBEDDING_MODEL=none,
or the provider fails) retrieval falls back to BM25 keyword search.
"""

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from src.config.settings import settings
from src.database.models import VectorStore

ANSWER_KEY = "answer_key"
REFERENCE = "reference"

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in", "is",
    "it", "its", "of", "on", "or", "that", "the", "this", "to", "was", "were", "what", "which",
    "with", "how", "why", "explain", "define", "describe", "state", "write", "give", "marks",
}


def tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS and len(t) > 1]


def chunk_text(text: str, chunk_words: int = settings.RAG_CHUNK_WORDS, overlap: int = 40) -> List[str]:
    """Split text into chunks of whole paragraphs; paragraphs longer than a chunk
    are split into overlapping word windows"""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    current: List[str] = []
    for paragraph in paragraphs:
        words = paragraph.split()
        if current and len(current) + len(words) > chunk_words:
            # A paragraph boundary is a natural break, so no overlap is carried over
            chunks.append(" ".join(current))
            current = []
        current.extend(words)
        while len(current) > chunk_words:
            chunks.append(" ".join(current[:chunk_words]))
            current = current[chunk_words - overlap:]
    if current:
        chunks.append(" ".join(current))
    return chunks


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def bm25_scores(query: str, documents: List[str], k1: float = 1.5, b: float = 0.75) -> List[float]:
    query_terms = set(tokenize(query))
    docs = [tokenize(d) for d in documents]
    if not query_terms or not docs:
        return [0.0] * len(documents)
    avg_len = sum(len(d) for d in docs) / len(docs) or 1
    doc_freq = Counter(term for d in docs for term in set(d))
    scores: List[float] = []
    for d in docs:
        counts = Counter(d)
        score = 0.0
        for term in query_terms:
            if term not in counts:
                continue
            idf = math.log(1 + (len(docs) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            tf = counts[term]
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(d) / avg_len))
        scores.append(score)
    return scores


def _prefix(question_bank_id: int) -> str:
    return f"qb:{int(question_bank_id)}:"


class ReferenceStore:
    """Indexes and retrieves reference material per question bank"""

    def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Embed texts, or return None so callers fall back to keyword search"""
        model = settings.EMBEDDING_MODEL
        if not texts or not model or model.lower() == "none":
            return None
        try:
            from litellm import embedding

            vectors: List[List[float]] = []
            for start in range(0, len(texts), 64):
                response = embedding(model=model, input=texts[start:start + 64])
                vectors.extend(item["embedding"] for item in response.data)
            return vectors
        except Exception as e:
            print(f"Embedding with {model} failed, using keyword search instead: {e}")
            return None

    # ---------- indexing ----------

    def add_answer_key(self, db: Session, question_bank_id: int, text: str, question_count: int, source: str) -> int:
        """Store a model answer per question. Replaces any earlier answer key."""
        from src.parsing.document_parser import document_parser

        answers = document_parser.extract_answers_from_text(text, question_count)
        self._delete(db, question_bank_id, ANSWER_KEY)
        stored = 0
        for key, answer in answers.items():
            if not answer.strip():
                continue
            db.add(VectorStore(
                content_type=ANSWER_KEY,
                content_id=f"{_prefix(question_bank_id)}key:{key}",
                content_text=answer,
                embedding=[],
                content_metadata={"question_bank_id": int(question_bank_id), "question_key": key, "source": source},
            ))
            stored += 1
        db.commit()
        return stored

    def add_course_material(self, db: Session, question_bank_id: int, text: str, source: str) -> int:
        """Chunk, embed and store course material. Returns the number of chunks."""
        chunks = chunk_text(text)
        if not chunks:
            return 0
        vectors = self.embed(chunks) or [[] for _ in chunks]
        start = db.query(VectorStore).filter(
            VectorStore.content_type == REFERENCE,
            VectorStore.content_id.like(f"{_prefix(question_bank_id)}%"),
        ).count()
        for offset, (chunk, vector) in enumerate(zip(chunks, vectors)):
            db.add(VectorStore(
                content_type=REFERENCE,
                content_id=f"{_prefix(question_bank_id)}ref:{start + offset}",
                content_text=chunk,
                embedding=vector,
                content_metadata={
                    "question_bank_id": int(question_bank_id),
                    "source": source,
                    "embedding_model": settings.EMBEDDING_MODEL if vector else None,
                },
            ))
        db.commit()
        return len(chunks)

    def clear(self, db: Session, question_bank_id: int) -> int:
        removed = self._delete(db, question_bank_id, ANSWER_KEY) + self._delete(db, question_bank_id, REFERENCE)
        db.commit()
        return removed

    def stats(self, db: Session, question_bank_id: int) -> Dict[str, int]:
        rows = self._rows(db, question_bank_id)
        return {
            "answer_key_questions": sum(1 for r in rows if r.content_type == ANSWER_KEY),
            "course_material_chunks": sum(1 for r in rows if r.content_type == REFERENCE),
        }

    # ---------- retrieval ----------

    def retrieve(self, db: Session, question_bank_id: int, query: str, top_k: int = settings.RAG_TOP_K) -> List[Tuple[str, float]]:
        """Most relevant course material chunks for a query"""
        rows = [r for r in self._rows(db, question_bank_id) if r.content_type == REFERENCE]
        if not rows or top_k <= 0:
            return []

        scores: Optional[List[float]] = None
        dims = {len(r.embedding or []) for r in rows}
        if len(dims) == 1 and 0 not in dims:
            query_vector = self.embed([query])
            if query_vector and len(query_vector[0]) in dims:
                scores = [cosine(query_vector[0], r.embedding) for r in rows]
        if scores is None:
            scores = bm25_scores(query, [r.content_text for r in rows])

        ranked = sorted(zip(rows, scores), key=lambda pair: pair[1], reverse=True)
        return [(row.content_text, score) for row, score in ranked[:top_k] if score > 0]

    def get_reference(self, db: Session, question_bank_id: int, question_key: str, question_text: str) -> Optional[str]:
        """Reference text for grading one question: its answer key plus relevant course material"""
        parts: List[str] = []
        key_row = db.query(VectorStore).filter(
            VectorStore.content_type == ANSWER_KEY,
            VectorStore.content_id == f"{_prefix(question_bank_id)}key:{question_key}",
        ).first()
        if key_row is not None:
            parts.append(f"Model answer from the answer key:\n{key_row.content_text}")

        passages = self.retrieve(db, question_bank_id, question_text)
        if passages:
            numbered = "\n\n".join(f"[{i}] {text}" for i, (text, _) in enumerate(passages, start=1))
            parts.append(f"Relevant course material:\n{numbered}")

        return "\n\n".join(parts) or None

    # ---------- helpers ----------

    def _rows(self, db: Session, question_bank_id: int) -> List[Any]:
        return db.query(VectorStore).filter(VectorStore.content_id.like(f"{_prefix(question_bank_id)}%")).all()

    def _delete(self, db: Session, question_bank_id: int, content_type: str) -> int:
        return db.query(VectorStore).filter(
            VectorStore.content_type == content_type,
            VectorStore.content_id.like(f"{_prefix(question_bank_id)}%"),
        ).delete(synchronize_session=False)


reference_store = ReferenceStore()
