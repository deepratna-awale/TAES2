"""
Database models for TAES 2 with proper SQLAlchemy type hints
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, List, Optional

Base = declarative_base()

class Student(Base):
    """Student model to store student information"""
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with evaluations
    evaluations = relationship("Evaluation", back_populates="student")

class QuestionBank(Base):
    """Question bank model to store questions and their metadata"""
    __tablename__ = "question_banks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    total_marks = Column(Integer, nullable=False)
    mark_distribution = Column(String(50), nullable=False)  # "in_paper" or "uniform"
    per_question_marks = Column(Integer)  # Only used for uniform distribution
    questions_json = Column(JSON, nullable=False)  # Store questions structure
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with evaluations
    evaluations = relationship("Evaluation", back_populates="question_bank")

class Evaluation(Base):
    """Evaluation model to store answer evaluation results"""
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    question_bank_id = Column(Integer, ForeignKey("question_banks.id"), nullable=False)
    
    # Evaluation details
    total_marks_obtained = Column(Float, nullable=False)
    total_marks_possible = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    
    # Answer details
    answer_file_name = Column(String(255), nullable=False)
    parsed_answers_json = Column(JSON, nullable=False)  # Store parsed answers
    evaluation_results_json = Column(JSON, nullable=False)  # Store detailed results
    remarks_json = Column(JSON)  # Store remarks where marks were cut
    
    # Metadata
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    student = relationship("Student", back_populates="evaluations")
    question_bank = relationship("QuestionBank", back_populates="evaluations")

class VectorStore(Base):
    """Vector store for question and answer embeddings"""
    __tablename__ = "vector_store"
    
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(50), nullable=False)  # "question", "answer", "reference"
    content_id = Column(String(100), nullable=False)  # question_id, answer_id, etc.
    content_text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)  # Store as JSON array
    content_metadata = Column(JSON)  # Additional metadata (renamed from metadata)
    created_at = Column(DateTime, default=datetime.utcnow)
