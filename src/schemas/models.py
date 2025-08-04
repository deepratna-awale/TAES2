"""
Pydantic schemas for TAES 2 with proper type safety
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationInfo
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# Enums for better type safety
class MarkDistribution(str, Enum):
    IN_PAPER = "in_paper"
    UNIFORM = "uniform"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class QuestionType(str, Enum):
    DEFINE = "define"
    EXPLAIN = "explain"
    SOLVE = "solve"
    PROVE = "prove"
    SHORT = "short"
    LONG = "long"

class ContentType(str, Enum):
    QUESTION = "question"
    ANSWER = "answer"
    REFERENCE = "reference"

# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

# Question and Answer schemas
class SubQuestion(BaseSchema):
    """Sub-question schema"""
    id: str = Field(..., description="Question ID (e.g., Q1a)")
    text: str = Field(..., description="Question text")
    type: QuestionType = Field(default=QuestionType.EXPLAIN, description="Question type")
    marks: int = Field(..., gt=0, description="Marks for this sub-question")

class Question(BaseSchema):
    """Main question schema"""
    id: str = Field(..., description="Question ID (e.g., Q1)")
    text: str = Field(..., description="Question text")
    type: QuestionType = Field(default=QuestionType.EXPLAIN, description="Question type")
    marks: int = Field(..., gt=0, description="Marks for this question")
    sub_questions: List[SubQuestion] = Field(default_factory=list, description="Sub-questions")

class QuestionBank(BaseSchema):
    """Question bank schema"""
    questions: List[Question] = Field(..., description="List of questions")
    total_marks: int = Field(..., gt=0, description="Total marks")
    question_count: int = Field(..., gt=0, description="Number of questions")

# Evaluation schemas
class EvaluationResult(BaseSchema):
    """Individual question evaluation result"""
    question_id: str = Field(..., description="Question ID")
    question_text: str = Field(..., description="Question text")
    student_answer: str = Field(..., description="Student's answer")
    marks_awarded: float = Field(..., ge=0, description="Marks awarded")
    total_marks: float = Field(..., gt=0, description="Total possible marks")
    percentage: float = Field(..., ge=0, le=100, description="Percentage score")
    justification: str = Field(..., description="Evaluation justification")
    remarks: str = Field(default="", description="Remarks if points were deducted")

class AnswerEvaluation(BaseSchema):
    """Complete answer evaluation"""
    student_name: str = Field(..., description="Student name")
    total_marks_obtained: float = Field(..., ge=0, description="Total marks obtained")
    total_marks_possible: float = Field(..., gt=0, description="Total possible marks")
    percentage: float = Field(..., ge=0, le=100, description="Overall percentage")
    evaluation_results: List[EvaluationResult] = Field(..., description="Individual question results")
    remarks: Dict[str, str] = Field(default_factory=dict, description="Remarks by question ID")
    status: ProcessingStatus = Field(default=ProcessingStatus.COMPLETED, description="Processing status")

# Database record schemas
class StudentCreate(BaseSchema):
    """Schema for creating a student"""
    name: str = Field(..., min_length=1, max_length=255, description="Student name")
    email: Optional[str] = Field(None, description="Student email")

class StudentResponse(BaseSchema):
    """Schema for student response"""
    id: int = Field(..., description="Student ID")
    name: str = Field(..., description="Student name")
    email: Optional[str] = Field(None, description="Student email")
    created_at: datetime = Field(..., description="Creation timestamp")

class QuestionBankCreate(BaseSchema):
    """Schema for creating a question bank"""
    name: str = Field(..., min_length=1, max_length=255, description="Question bank name")
    description: Optional[str] = Field(None, description="Description")
    total_marks: int = Field(..., gt=0, description="Total marks")
    mark_distribution: MarkDistribution = Field(..., description="Mark distribution method")
    per_question_marks: Optional[int] = Field(None, gt=0, description="Marks per question (uniform only)")
    questions_json: QuestionBank = Field(..., description="Questions structure")

    @field_validator('per_question_marks')
    @classmethod
    def validate_per_question_marks(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Validate per_question_marks based on mark_distribution"""
        values = info.data
        if values.get('mark_distribution') == MarkDistribution.UNIFORM and v is None:
            raise ValueError('per_question_marks is required for uniform distribution')
        if values.get('mark_distribution') == MarkDistribution.IN_PAPER and v is not None:
            raise ValueError('per_question_marks should not be set for in_paper distribution')
        return v

class QuestionBankResponse(BaseSchema):
    """Schema for question bank response"""
    id: int = Field(..., description="Question bank ID")
    name: str = Field(..., description="Question bank name")
    description: Optional[str] = Field(None, description="Description")
    total_marks: int = Field(..., description="Total marks")
    mark_distribution: MarkDistribution = Field(..., description="Mark distribution method")
    per_question_marks: Optional[int] = Field(None, description="Marks per question")
    questions_json: QuestionBank = Field(..., description="Questions structure")
    created_at: datetime = Field(..., description="Creation timestamp")

class EvaluationCreate(BaseSchema):
    """Schema for creating an evaluation"""
    student_id: int = Field(..., description="Student ID")
    question_bank_id: int = Field(..., description="Question bank ID")
    answer_file_name: str = Field(..., description="Answer file name")
    parsed_answers_json: Dict[str, str] = Field(..., description="Parsed answers")
    evaluation_results_json: List[EvaluationResult] = Field(..., description="Evaluation results")
    remarks_json: Optional[Dict[str, str]] = Field(None, description="Remarks")
    total_marks_obtained: float = Field(..., ge=0, description="Total marks obtained")
    total_marks_possible: float = Field(..., gt=0, description="Total possible marks")
    percentage: float = Field(..., ge=0, le=100, description="Percentage score")

class EvaluationResponse(BaseSchema):
    """Schema for evaluation response"""
    id: int = Field(..., description="Evaluation ID")
    student_id: int = Field(..., description="Student ID")
    question_bank_id: int = Field(..., description="Question bank ID")
    total_marks_obtained: float = Field(..., description="Total marks obtained")
    total_marks_possible: float = Field(..., description="Total possible marks")
    percentage: float = Field(..., description="Percentage score")
    answer_file_name: str = Field(..., description="Answer file name")
    processing_status: ProcessingStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

# LLM schemas
class LLMRequest(BaseSchema):
    """Schema for LLM requests"""
    model: str = Field(..., description="Model name")
    messages: List[Dict[str, str]] = Field(..., description="Chat messages")
    temperature: float = Field(default=0.3, ge=0, le=2, description="Temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens")

class LLMResponse(BaseSchema):
    """Schema for LLM responses"""
    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model used")
    usage: Optional[Dict[str, Any]] = Field(None, description="Usage statistics")

# File upload schemas
class FileUpload(BaseSchema):
    """Schema for file uploads"""
    filename: str = Field(..., description="File name")
    content_type: str = Field(..., description="MIME type")
    size: int = Field(..., gt=0, description="File size in bytes")

class DocumentParseResult(BaseSchema):
    """Schema for document parsing results"""
    text_content: str = Field(..., description="Extracted text")
    answers: Dict[str, str] = Field(..., description="Parsed answers by question ID")
    student_name: str = Field(..., description="Extracted student name")

# Vector store schemas
class VectorStoreCreate(BaseSchema):
    """Schema for creating vector store entries"""
    content_type: ContentType = Field(..., description="Content type")
    content_id: str = Field(..., description="Content identifier")
    content_text: str = Field(..., description="Text content")
    embedding: List[float] = Field(..., description="Vector embedding")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class VectorStoreResponse(BaseSchema):
    """Schema for vector store responses"""
    id: int = Field(..., description="Vector store ID")
    content_type: ContentType = Field(..., description="Content type")
    content_id: str = Field(..., description="Content identifier")
    content_text: str = Field(..., description="Text content")
    embedding: List[float] = Field(..., description="Vector embedding")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")

# Database statistics schema
class DatabaseStats(BaseSchema):
    """Schema for database statistics"""
    student_count: int = Field(..., ge=0, description="Number of students")
    question_bank_count: int = Field(..., ge=0, description="Number of question banks")
    evaluation_count: int = Field(..., ge=0, description="Number of evaluations")
    average_score: Optional[float] = Field(None, ge=0, le=100, description="Average score")

# Batch processing schemas
class BatchProcessingStatus(BaseSchema):
    """Schema for batch processing status"""
    total_files: int = Field(..., ge=0, description="Total files to process")
    completed: int = Field(..., ge=0, description="Completed files")
    failed: int = Field(..., ge=0, description="Failed files")
    in_progress: int = Field(..., ge=0, description="Files in progress")
    average_score: Optional[float] = Field(None, ge=0, le=100, description="Average score")

# Configuration schemas
class DatabaseConfig(BaseSchema):
    """Schema for database configuration"""
    url: str = Field(..., description="Database URL")
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=5, gt=0, description="Connection pool size")

class LLMConfig(BaseSchema):
    """Schema for LLM configuration"""
    default_model: str = Field(..., description="Default model name")
    default_temperature: float = Field(default=0.3, ge=0, le=2, description="Default temperature")
    default_max_tokens: int = Field(default=2000, gt=0, description="Default max tokens")
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")
