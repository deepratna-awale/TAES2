"""
Helpers shared by the Gradio interfaces
"""

import os
from typing import Any, List, Optional, Tuple

import gradio as gr

from src.config.settings import settings
from src.database.init_db import get_db
from src.database.models import QuestionBank

MODEL_CHOICES: List[str] = settings.MODEL_CHOICES
DEFAULT_MODEL: str = settings.DEFAULT_MODEL


def file_path(file: Any) -> Optional[str]:
    """Return the local path of an uploaded file.

    Gradio 4+ passes a path string, older versions passed a tempfile wrapper.
    """
    if file is None:
        return None
    if isinstance(file, (str, os.PathLike)):
        return str(file)
    return getattr(file, "path", None) or getattr(file, "name", None)


def read_upload(file: Any) -> Tuple[bytes, str]:
    """Read an uploaded file, returning its bytes and its original file name"""
    path = file_path(file)
    if not path:
        raise ValueError("No file uploaded")
    with open(path, "rb") as f:
        content = f.read()
    return content, os.path.basename(getattr(file, "orig_name", None) or path)


def question_bank_choices(label_format: str = "{name} (ID: {id})") -> List[Tuple[str, int]]:
    """List saved question banks as (label, id) dropdown choices"""
    db = None
    try:
        db = next(get_db())
        return [
            (label_format.format(name=qb.name, id=qb.id, total_marks=qb.total_marks), qb.id)
            for qb in db.query(QuestionBank).order_by(QuestionBank.id).all()
        ]
    except Exception as e:
        print(f"Error refreshing question banks: {e}")
        return []
    finally:
        if db is not None:
            db.close()


def refresh_question_banks_update(label_format: str = "{name} (ID: {id})"):
    """Dropdown update with the current question banks, keeping the first selected"""
    choices = question_bank_choices(label_format)
    return gr.update(choices=choices, value=choices[0][1] if choices else None)
