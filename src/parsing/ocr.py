"""
Transcription of handwritten and scanned documents with a vision-capable LLM
"""

import base64
import io
from typing import Any, Dict, List, Optional

import pdfplumber
from PIL import Image, ImageOps

from src.config.settings import settings

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "tif", "tiff", "bmp"}

TRANSCRIBE_PROMPT = """Transcribe all handwritten and printed text on this exam page exactly as written.

Rules:
- Keep question and answer numbers (e.g. "Q1.", "2)", "Ans 3.", "a)") at the start of their own lines.
- Keep the original line breaks and order. Write equations in plain text.
- Do not correct spelling, grammar or mistakes, and do not answer or explain anything.
- Write [illegible] for any word you cannot read.
- Output only the transcription, with no commentary."""


def pdf_page_images(file_content: bytes, max_pages: int, resolution: int) -> List[Image.Image]:
    """Render PDF pages to images"""
    images: List[Image.Image] = []
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages[:max_pages]:
            images.append(page.to_image(resolution=resolution).original.copy())
    return images


def load_images(file_content: bytes, max_pages: int) -> List[Image.Image]:
    """Open an image file, including every frame of a multi-page TIFF"""
    image = Image.open(io.BytesIO(file_content))
    frames: List[Image.Image] = []
    for index in range(min(getattr(image, "n_frames", 1), max_pages)):
        image.seek(index)
        # Phone photos are often stored sideways with an EXIF rotation flag
        frames.append(ImageOps.exif_transpose(image.copy()))
    return frames


def image_to_data_url(image: Image.Image, max_side: int = 2000) -> str:
    """Encode an image as a JPEG data URL small enough for vision APIs"""
    image = image.convert("RGB")
    image.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


class HandwritingTranscriber:
    """Turns page images into text, one vision LLM call per page"""

    def transcribe_images(self, images: List[Image.Image], model: Optional[str] = None) -> str:
        # Imported here so document parsing works without LLM setup when OCR is never used
        from src.llm.manager import llm_manager

        vision_model = settings.VISION_MODEL or model or llm_manager.default_model
        pages: List[str] = []
        for image in images:
            messages: List[Dict[str, Any]] = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": TRANSCRIBE_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_to_data_url(image)}},
                ],
            }]
            text = llm_manager.get_completion(messages, model=vision_model, temperature=0, max_tokens=4000)
            pages.append(text.strip())
        return "\n".join(page for page in pages if page)

    def transcribe_pdf(self, file_content: bytes, model: Optional[str] = None) -> str:
        images = pdf_page_images(file_content, settings.MAX_OCR_PAGES, settings.OCR_RESOLUTION)
        return self.transcribe_images(images, model)

    def transcribe_image_file(self, file_content: bytes, model: Optional[str] = None) -> str:
        return self.transcribe_images(load_images(file_content, settings.MAX_OCR_PAGES), model)


transcriber = HandwritingTranscriber()
