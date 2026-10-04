import pytest

from src.config.settings import settings
from src.database.init_db import get_db, initialize_database
from src.database.models import QuestionBank
from src.evaluation.engine import evaluation_engine
from src.llm.manager import EvaluationResult
from src.rag import store as store_module
from src.rag.store import bm25_scores, chunk_text, reference_store

COURSE_NOTES = """Photosynthesis happens in the chloroplast. Light energy splits water and
releases oxygen, and the Calvin cycle fixes carbon dioxide into glucose.

Mitochondria are the site of cellular respiration. Glucose is oxidised to carbon
dioxide and water, and the energy is stored as ATP.

Osmosis is the movement of water across a semi permeable membrane from a dilute
solution to a concentrated one."""

QUESTIONS = {
    "questions": [
        {"id": "Q1", "text": "Explain photosynthesis and where it happens", "type": "explain", "marks": 5},
        {"id": "Q2", "text": "What is osmosis?", "type": "define", "marks": 5},
    ],
    "total_marks": 10,
    "question_count": 2,
}


@pytest.fixture
def keyword_only(monkeypatch):
    monkeypatch.setattr(settings, "EMBEDDING_MODEL", "none")


@pytest.fixture
def question_bank_id():
    initialize_database()
    db = next(get_db())
    qb = QuestionBank(name="Biology", total_marks=10, mark_distribution="in_paper", questions_json=QUESTIONS)
    db.add(qb)
    db.commit()
    qb_id = qb.id
    db.close()
    return qb_id


def test_chunk_text_respects_size_and_overlaps():
    text = " ".join(f"w{i}" for i in range(500))
    chunks = chunk_text(text, chunk_words=100, overlap=20)
    assert all(len(c.split()) <= 100 for c in chunks)
    assert chunks[1].split()[0] == "w80"
    assert chunks[-1].split()[-1] == "w499"


def test_short_paragraphs_are_not_repeated_across_chunks():
    text = "Osmosis moves water.\n\n" + "filler " * 200 + "\n\nPhotosynthesis makes sugar."
    chunks = chunk_text(text, chunk_words=180, overlap=40)
    assert sum("Osmosis" in c for c in chunks) == 1


def test_bm25_prefers_matching_passage():
    docs = ["the mitochondria make ATP", "osmosis moves water across a membrane", "unrelated text"]
    scores = bm25_scores("What is osmosis?", docs)
    assert scores.index(max(scores)) == 1


def test_keyword_retrieval_finds_relevant_passage(keyword_only, question_bank_id):
    db = next(get_db())
    reference_store.add_course_material(db, question_bank_id, COURSE_NOTES.replace("\n\n", "\n\n" + "filler " * 200 + "\n\n"), "notes.pdf")
    passages = reference_store.retrieve(db, question_bank_id, "What is osmosis?", top_k=1)
    db.close()
    assert "semi permeable membrane" in passages[0][0]


def test_answer_key_is_matched_by_question_number(keyword_only, question_bank_id):
    db = next(get_db())
    stored = reference_store.add_answer_key(
        db, question_bank_id, "1. Light energy is turned into glucose in chloroplasts.\n2. Diffusion of water.", 2, "key.pdf"
    )
    assert stored == 2
    reference = reference_store.get_reference(db, question_bank_id, "Q2", "What is osmosis?")
    assert "Diffusion of water" in reference
    assert "chloroplasts" not in reference
    # Uploading a new key replaces the old one
    reference_store.add_answer_key(db, question_bank_id, "1. New answer one", 2, "key2.pdf")
    assert reference_store.stats(db, question_bank_id)["answer_key_questions"] == 1
    db.close()


def test_reference_is_scoped_to_question_bank(keyword_only, question_bank_id):
    db = next(get_db())
    reference_store.add_course_material(db, question_bank_id, COURSE_NOTES, "notes.pdf")
    assert reference_store.get_reference(db, question_bank_id + 1000, "Q1", "photosynthesis") is None
    assert reference_store.clear(db, question_bank_id) > 0
    assert reference_store.get_reference(db, question_bank_id, "Q1", "photosynthesis") is None
    db.close()


def test_embedding_retrieval(monkeypatch, question_bank_id):
    vocab = ["photosynthesis", "osmosis", "mitochondria"]

    def fake_embed(self, texts):
        return [[float(word in t.lower()) for word in vocab] + [0.01] for t in texts]

    monkeypatch.setattr(store_module.ReferenceStore, "embed", fake_embed)
    db = next(get_db())
    reference_store.add_course_material(
        db, question_bank_id,
        "Osmosis moves water.\n\n" + "pad " * 200 + "\n\nPhotosynthesis makes sugar.", "notes.txt",
    )
    passages = reference_store.retrieve(db, question_bank_id, "osmosis", top_k=1)
    db.close()
    assert "Osmosis moves water" in passages[0][0]


def test_engine_grades_with_reference(keyword_only, monkeypatch, question_bank_id):
    seen = {}

    def fake_evaluate(question, student_answer, marks, question_type="explain", model=None, reference_answer=None):
        seen[question] = reference_answer
        return EvaluationResult(marks_awarded=marks, total_marks=marks, justification="ok")

    monkeypatch.setattr(evaluation_engine.llm_manager, "evaluate_answer", fake_evaluate)
    db = next(get_db())
    reference_store.add_answer_key(db, question_bank_id, "Q1. Chloroplasts turn light into glucose", 2, "key.txt")
    reference_store.add_course_material(db, question_bank_id, COURSE_NOTES, "notes.txt")
    db.close()

    result = evaluation_engine.process_single_answer_sheet(
        b"Q1. It happens in leaves\nQ2. Water moving", "amy.txt", question_bank_id
    )

    assert result.status == "completed", result.error
    assert "Chloroplasts turn light into glucose" in seen["Explain photosynthesis and where it happens"]
    assert "semi permeable" in seen["What is osmosis?"]
    assert all(r["reference_used"] for r in result.evaluation_results)
