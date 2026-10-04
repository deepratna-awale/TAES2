"""
Document parsing utilities for PDF and DOCX files
"""

import re
import io
import os
from typing import Dict, List, Optional, Set, Match
import pypdf
import pdfplumber
from docx import Document
from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    """Type-safe parsed document content"""
    text: str = Field(..., description="Extracted text content")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx)")
    page_count: Optional[int] = Field(default=None, description="Number of pages")


class ExtractedAnswers(BaseModel):
    """Type-safe extracted answers from document"""
    answers: Dict[str, str] = Field(..., description="Question ID to answer mapping")
    question_count: int = Field(..., gt=0, description="Expected number of questions")
    student_name: str = Field(..., description="Extracted student name")


class DocumentParser:
    """Handles parsing of PDF and DOCX documents"""
    
    def __init__(self) -> None:
        self.answer_patterns: List[str] = [
            r'^(\d+)[\.\)]\s*',  # 1. or 1)
            r'^Q(\d+)[\.\)]\s*',  # Q1. or Q1)
            r'^Question\s*(\d+)[\.\)]\s*',  # Question 1. or Question 1)
            r'^Ans[\.\s]*(\d+)[\.\)]\s*',  # Ans. 1 or Ans 1)
        ]
    
    def parse_pdf(self, file_content: bytes) -> str:
        """Parse PDF file and extract text"""
        try:
            # Try with pdfplumber first (better for complex layouts)
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text_content: List[str] = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                
                if text_content:
                    return '\n'.join(text_content)
            
            # Fallback to pypdf
            pdf_file = io.BytesIO(file_content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            text_content = []
            
            for page in pdf_reader.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text_content.append(extracted_text)
            
            return '\n'.join(text_content)
            
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            raise
    
    def parse_docx(self, file_content: bytes) -> str:
        """Parse DOCX file and extract text"""
        try:
            doc = Document(io.BytesIO(file_content))
            text_content: List[str] = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text and paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            return '\n'.join(text_content)
            
        except Exception as e:
            print(f"Error parsing DOCX: {e}")
            raise
    
    def parse_txt(self, file_content: bytes) -> str:
        """Decode a plain text file"""
        for encoding in ('utf-8-sig', 'utf-16'):
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return file_content.decode('latin-1')
    
    def parse_document(self, file_content: bytes, filename: str) -> str:
        """Parse document based on file extension"""
        file_extension: str = filename.lower().rsplit('.', 1)[-1]
        
        if file_extension == 'pdf':
            return self.parse_pdf(file_content)
        elif file_extension == 'docx':
            return self.parse_docx(file_content)
        elif file_extension == 'txt':
            return self.parse_txt(file_content)
        elif file_extension == 'doc':
            raise ValueError("Legacy .doc files are not supported, please save the file as .docx or PDF")
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def extract_answers_from_text(self, text: str, question_count: int) -> Dict[str, str]:
        """Extract individual answers from parsed text"""
        answers: Dict[str, str] = {}
        lines: List[str] = text.split('\n')
        current_answer: Optional[str] = None
        current_content: List[str] = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with answer pattern
            answer_match: Optional[Match[str]] = None
            for pattern in self.answer_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    answer_match = match
                    break
            
            if answer_match:
                # Save previous answer if exists
                if current_answer and current_content:
                    answers[current_answer] = '\n'.join(current_content).strip()
                
                # Start new answer
                answer_num: str = answer_match.group(1)
                current_answer = f"Q{answer_num}"
                
                # Get content after the answer number
                remaining_text: str = line[answer_match.end():].strip()
                current_content = [remaining_text] if remaining_text else []
            else:
                # Continue current answer
                if current_answer:
                    current_content.append(line)
        
        # Save last answer
        if current_answer and current_content:
            answers[current_answer] = '\n'.join(current_content).strip()
        
        # Fill missing answers and guess numbering
        complete_answers: Dict[str, str] = self._fill_missing_answers(answers, question_count)
        
        return complete_answers
    
    def _fill_missing_answers(self, answers: Dict[str, str], expected_count: int) -> Dict[str, str]:
        """Return Q1..Qn, filling gaps with answers numbered outside that range.

        Students sometimes number answers differently from the paper (e.g. 0-based or
        skipping numbers), so leftover out-of-range answers are mapped onto missing
        slots in order. An answer is never used for two questions.
        """
        def number_of(key: str) -> Optional[int]:
            try:
                return int(key[1:]) if key.startswith('Q') else None
            except ValueError:
                return None
        
        leftovers: List[str] = [
            content for key, content in sorted(answers.items(), key=lambda kv: number_of(kv[0]) or 0)
            if (number_of(key) is None or not 1 <= number_of(key) <= expected_count) and content
        ]
        
        complete_answers: Dict[str, str] = {}
        for i in range(1, expected_count + 1):
            question_key: str = f"Q{i}"
            if answers.get(question_key):
                complete_answers[question_key] = answers[question_key]
            else:
                complete_answers[question_key] = leftovers.pop(0) if leftovers else ""
        
        return complete_answers
    
    def extract_student_name_from_filename(self, filename: str) -> str:
        """Extract student name from filename"""
        # Uploads arrive as full temp paths, keep only the file name
        name: str = os.path.basename(filename)
        # Remove file extension
        name = name.rsplit('.', 1)[0]
        
        # Clean up common patterns
        name = re.sub(r'[_\-]+', ' ', name)  # Replace underscores/hyphens with spaces
        name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
        name = name.strip()
        
        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name


# Global parser instance
document_parser = DocumentParser()
