from src.parsing.document_parser import document_parser
from src.utils.test_data import SAMPLE_ANSWER_SHEET_1, SAMPLE_ANSWER_SHEET_2


def test_extracts_numbered_answers():
    answers = document_parser.extract_answers_from_text(SAMPLE_ANSWER_SHEET_1, 5)
    assert list(answers) == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert "function" in answers["Q1"].lower()
    assert "induction" in answers["Q4"].lower()


def test_extracts_q_prefixed_answers():
    answers = document_parser.extract_answers_from_text(SAMPLE_ANSWER_SHEET_2, 5)
    assert all(answers[f"Q{i}"] for i in range(1, 6))
    assert answers["Q5"].startswith("a) cos(x)")


def test_missing_answer_is_not_filled_with_another_answer():
    text = "Q1. first answer\nQ3. third answer"
    answers = document_parser.extract_answers_from_text(text, 3)
    assert answers == {"Q1": "first answer", "Q2": "", "Q3": "third answer"}


def test_out_of_range_answers_fill_gaps():
    text = "Q1. first\nQ7. misnumbered"
    answers = document_parser.extract_answers_from_text(text, 2)
    assert answers == {"Q1": "first", "Q2": "misnumbered"}


def test_student_name_ignores_upload_directory():
    name = document_parser.extract_student_name_from_filename("/tmp/gradio/abc123/john_smith.pdf")
    assert name == "John Smith"


def test_parses_txt_files():
    text = document_parser.parse_document("Q1. hello".encode(), "sheet.txt")
    assert text == "Q1. hello"


def test_rejects_legacy_doc_with_clear_message():
    try:
        document_parser.parse_document(b"", "sheet.doc")
    except ValueError as e:
        assert ".docx" in str(e)
    else:
        raise AssertionError("expected ValueError")
