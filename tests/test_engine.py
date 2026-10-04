from src.database.init_db import get_db, initialize_database
from src.database.models import Evaluation, QuestionBank
from src.evaluation.engine import evaluation_engine
from src.llm.manager import EvaluationResult
from src.utils.test_data import SAMPLE_ANSWER_SHEET_2


QUESTIONS = {
    "questions": [
        {"id": "Q1", "text": "Define:", "type": "define", "marks": 10, "sub_questions": [
            {"id": "Q1a", "text": "Function", "type": "define", "marks": 5},
            {"id": "Q1b", "text": "Domain and Range", "type": "define", "marks": 5},
        ]},
        {"id": "Q2", "text": "Solve:", "type": "solve", "marks": 20, "sub_questions": []},
        {"id": "Q3", "text": "Explain limits", "type": "explain", "marks": 25, "sub_questions": []},
        {"id": "Q4", "text": "Prove the sum formula", "type": "prove", "marks": 20, "sub_questions": []},
        {"id": "Q5", "text": "Short answers", "type": "short", "marks": 25, "sub_questions": []},
    ],
    "total_marks": 100,
    "question_count": 5,
}


def _create_question_bank():
    initialize_database()
    db = next(get_db())
    qb = QuestionBank(name="Maths", total_marks=100, mark_distribution="in_paper", questions_json=QUESTIONS)
    db.add(qb)
    db.commit()
    db.refresh(qb)
    qb_id = qb.id
    db.close()
    return qb_id


def test_evaluates_sheet_without_double_counting(monkeypatch):
    graded = []

    def fake_evaluate(question, student_answer, marks, question_type="explain", model=None, reference_answer=None):
        graded.append((question, marks))
        return EvaluationResult(marks_awarded=marks / 2, total_marks=marks, justification="half", remarks="partial")

    monkeypatch.setattr(evaluation_engine.llm_manager, "evaluate_answer", fake_evaluate)
    qb_id = _create_question_bank()

    result = evaluation_engine.process_single_answer_sheet(
        SAMPLE_ANSWER_SHEET_2.encode(), "/tmp/gradio/xyz/jane_doe.txt", qb_id, "gpt-4o-mini"
    )

    assert result.status == "completed", result.error
    assert result.student_name == "Jane Doe"
    # One grading call per main question; sub-parts are graded as part of their question
    assert len(graded) == 5
    assert "Domain and Range" in graded[0][0]
    assert result.total_marks_possible == 100
    assert result.total_marks_obtained == 50
    assert result.percentage == 50

    db = next(get_db())
    saved = db.get(Evaluation, result.evaluation_id)
    assert saved.answer_file_name == "jane_doe.txt"
    db.close()


def test_unknown_question_bank_fails_cleanly():
    initialize_database()
    result = evaluation_engine.process_single_answer_sheet(b"Q1. x", "a.txt", 999999)
    assert result.status == "failed"
    assert "not found" in result.error
