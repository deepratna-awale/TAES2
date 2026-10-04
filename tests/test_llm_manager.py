import json

import pytest

from src.llm import manager as llm_module
from src.llm.manager import EvaluationResult, LLMManager, extract_json


def test_extract_json_handles_markdown_fences():
    assert extract_json('Here you go:\n```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_handles_surrounding_prose():
    assert extract_json('Result: {"a": {"b": 2}} hope that helps') == {"a": {"b": 2}}


def test_evaluation_result_clamps_and_computes_percentage():
    result = EvaluationResult(marks_awarded=12, total_marks=10, percentage=999, justification="x")
    assert result.marks_awarded == 10
    assert result.percentage == 100


def test_evaluation_result_accepts_fractional_marks():
    result = EvaluationResult(marks_awarded=7.5, total_marks=10, justification="x")
    assert result.percentage == 75


@pytest.fixture
def fake_completion(monkeypatch):
    calls = []

    def install(content):
        def _completion(**kwargs):
            calls.append(kwargs)

            class Msg:
                pass

            msg = Msg()
            msg.content = content

            class Choice:
                message = msg

            class Resp:
                choices = [Choice()]

            return Resp()

        monkeypatch.setattr(llm_module, "completion", _completion)
        return calls

    return install


def test_evaluate_answer_uses_question_marks(fake_completion):
    fake_completion('```json\n{"marks_awarded": 4, "total_marks": 99, "justification": "ok", "remarks": "missing example"}\n```')
    result = LLMManager().evaluate_answer("Q?", "A", marks=5)
    assert result.total_marks == 5
    assert result.percentage == 80


def test_parse_questions_is_lenient(fake_completion):
    fake_completion(json.dumps({
        "questions": [
            {"id": "Q1", "text": "Solve", "type": "solve", "marks": 10, "sub_questions": []},
            {"id": "Q2", "text": "Prove", "type": "explain|define", "marks": 10},
        ],
        "total_marks": 20,
        "question_count": 5,
    }))
    result = LLMManager().parse_questions_from_text("paper", 20, "in_paper")
    assert result.question_count == 2
    assert [q.type for q in result.questions] == ["solve", "explain"]


def test_uniform_distribution_overrides_marks(fake_completion):
    fake_completion(json.dumps({
        "questions": [{"id": "Q1", "text": "a", "marks": 3}, {"id": "Q2", "text": "b", "marks": 7}],
        "total_marks": 20,
    }))
    result = LLMManager().parse_questions_from_text("paper", 20, "uniform", per_question_marks=10)
    assert [q.marks for q in result.questions] == [10, 10]


def test_temperature_zero_is_respected(fake_completion):
    calls = fake_completion('{"marks_awarded": 1, "total_marks": 1}')
    LLMManager().get_completion([{"role": "user", "content": "x"}], temperature=0)
    assert calls[0]["temperature"] == 0


def test_ollama_models_get_api_base(fake_completion):
    calls = fake_completion("{}")
    LLMManager().get_completion([{"role": "user", "content": "x"}], model="ollama/llama3")
    assert calls[0]["api_base"]
