import io

from PIL import Image
from pypdf import PdfWriter

from src.llm import manager as llm_module
from src.parsing import ocr
from src.parsing.document_parser import document_parser


def _png_bytes(size=(60, 40)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, "white").save(buffer, format="PNG")
    return buffer.getvalue()


def _blank_pdf(pages=2) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(200, 200)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _fake_vision(monkeypatch, text="Q1. handwritten answer"):
    calls = []

    def _completion(**kwargs):
        calls.append(kwargs)

        class Msg:
            content = text

        class Choice:
            message = Msg()

        class Resp:
            choices = [Choice()]

        return Resp()

    monkeypatch.setattr(llm_module, "completion", _completion)
    return calls


def test_images_are_transcribed(monkeypatch):
    calls = _fake_vision(monkeypatch)
    text = document_parser.parse_document(_png_bytes(), "sheet.jpg", model="gpt-4o-mini")
    assert text == "Q1. handwritten answer"
    content = calls[0]["messages"][0]["content"]
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert calls[0]["model"] == "gpt-4o-mini"
    assert calls[0]["temperature"] == 0


def test_scanned_pdf_is_detected_and_transcribed_per_page(monkeypatch):
    calls = _fake_vision(monkeypatch)
    text = document_parser.parse_document(_blank_pdf(pages=2), "scan.pdf")
    assert len(calls) == 2
    assert text.count("handwritten answer") == 2


def test_vision_model_setting_overrides_selected_model(monkeypatch):
    calls = _fake_vision(monkeypatch)
    monkeypatch.setattr(ocr.settings, "VISION_MODEL", "gemini/gemini-2.0-flash")
    document_parser.parse_document(_png_bytes(), "sheet.png", model="gpt-4o-mini")
    assert calls[0]["model"] == "gemini/gemini-2.0-flash"


def test_typed_pdf_skips_ocr_unless_handwritten(monkeypatch):
    calls = _fake_vision(monkeypatch)
    monkeypatch.setattr(document_parser, "parse_pdf", lambda content: "Q1. " + "typed words " * 30)
    pdf = _blank_pdf(pages=1)
    assert document_parser.parse_document(pdf, "typed.pdf").startswith("Q1. typed")
    assert calls == []
    document_parser.parse_document(pdf, "typed.pdf", handwritten=True)
    assert len(calls) == 1


def test_large_photos_are_downscaled():
    url = ocr.image_to_data_url(Image.new("RGB", (5000, 3000), "white"), max_side=2000)
    import base64
    decoded = Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1])))
    assert max(decoded.size) == 2000


def test_page_limit(monkeypatch):
    calls = _fake_vision(monkeypatch)
    monkeypatch.setattr(ocr.settings, "MAX_OCR_PAGES", 1)
    document_parser.parse_document(_blank_pdf(pages=3), "scan.pdf")
    assert len(calls) == 1
