"""
Answer evaluation engine
"""

from typing import Dict, List, Any, Optional, Tuple
from src.llm.manager import llm_manager, EvaluationResult
from src.parsing.document_parser import document_parser
from src.database.models import Evaluation, Student, QuestionBank
from src.database.init_db import get_db
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class ProcessingResult(BaseModel):
    """Type-safe processing result"""
    evaluation_id: Optional[int] = Field(default=None, description="Database evaluation ID")
    student_name: str = Field(..., description="Name of the student")
    total_marks_obtained: Optional[int] = Field(default=None, description="Total marks obtained")
    total_marks_possible: Optional[int] = Field(default=None, description="Total marks possible")
    percentage: Optional[float] = Field(default=None, description="Final percentage score")
    evaluation_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Individual question results")
    remarks: Optional[Dict[str, str]] = Field(default=None, description="Remarks for questions with deductions")
    status: str = Field(..., description="Processing status")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class QuestionResult(BaseModel):
    """Type-safe question evaluation result"""
    question_id: str = Field(..., description="Question identifier")
    question_text: str = Field(..., description="Question text")
    student_answer: str = Field(..., description="Student's answer")
    marks_awarded: int = Field(..., ge=0, description="Marks awarded")
    total_marks: int = Field(..., gt=0, description="Total marks possible")
    percentage: float = Field(..., ge=0, le=100, description="Percentage score")
    justification: str = Field(..., description="Evaluation justification")
    remarks: str = Field(default="", description="Specific remarks")


class EvaluationEngine:
    """Main engine for evaluating student answers"""
    
    def __init__(self) -> None:
        self.llm_manager = llm_manager
        self.document_parser = document_parser
    
    def process_single_answer_sheet(
        self,
        file_content: bytes,
        filename: str,
        question_bank_id: int,
        model_name: Optional[str] = None
    ) -> ProcessingResult:
        """Process a single answer sheet"""
        
        db: Optional[Session] = None
        try:
            # Parse document
            text_content: str = self.document_parser.parse_document(file_content, filename)
            
            # Get question bank from database
            db = next(get_db())
            question_bank = db.get(QuestionBank, question_bank_id)
            if not question_bank:
                raise ValueError(f"Question bank with ID {question_bank_id} not found")
            
            questions: List[Dict[str, Any]] = question_bank.questions_json["questions"]
            question_count: int = len(questions)
            
            # Extract answers from text
            parsed_answers: Dict[str, str] = self.document_parser.extract_answers_from_text(text_content, question_count)
            
            # Extract student name from filename
            student_name: str = self.document_parser.extract_student_name_from_filename(filename)
            
            # Get or create student
            # Using type: ignore for SQLAlchemy column comparison typing issue
            existing_students = db.query(Student).filter(Student.name == student_name).all()  # type: ignore
            student = existing_students[0] if existing_students else None
            
            if not student:
                student = Student(name=student_name, email=f"{student_name.lower().replace(' ', '.')}@example.com")
                db.add(student)
                db.commit()
                db.refresh(student)
            
            # Evaluate each answer
            evaluation_results: List[Dict[str, Any]] = []
            total_marks_obtained: int = 0
            total_marks_possible: int = 0
            remarks: Dict[str, str] = {}
            
            for question in questions:
                question_id: str = question["id"]
                question_text: str = question["text"]
                question_marks: int = question["marks"]
                question_type: str = question.get("type", "explain")
                
                # Get student answer
                student_answer: str = parsed_answers.get(question_id, "")
                
                if student_answer.strip():
                    # Evaluate answer using LLM
                    evaluation: EvaluationResult = self.llm_manager.evaluate_answer(
                        question=question_text,
                        student_answer=student_answer,
                        marks=question_marks,
                        question_type=question_type,
                        model=model_name
                    )
                    
                    marks_awarded: int = evaluation.marks_awarded
                    total_marks_obtained += marks_awarded
                    total_marks_possible += question_marks
                    
                    # Store remarks if points were cut
                    if marks_awarded < question_marks and evaluation.remarks.strip():
                        remarks[question_id] = evaluation.remarks
                    
                    # Store results using QuestionResult model for type safety
                    question_result = QuestionResult(
                        question_id=question_id,
                        question_text=question_text,
                        student_answer=student_answer,
                        marks_awarded=marks_awarded,
                        total_marks=question_marks,
                        percentage=evaluation.percentage,
                        justification=evaluation.justification,
                        remarks=evaluation.remarks
                    )
                    evaluation_results.append(question_result.model_dump())
                    
                    # Handle sub-questions
                    for sub_question in question.get("sub_questions", []):
                        sub_question_id: str = sub_question["id"]
                        sub_question_text: str = sub_question["text"]
                        sub_question_marks: int = sub_question["marks"]
                        sub_question_type: str = sub_question.get("type", "explain")
                        
                        # Get student answer for sub-question
                        sub_student_answer: str = parsed_answers.get(sub_question_id, "")
                        
                        if sub_student_answer.strip():
                            sub_evaluation: EvaluationResult = self.llm_manager.evaluate_answer(
                                question=sub_question_text,
                                student_answer=sub_student_answer,
                                marks=sub_question_marks,
                                question_type=sub_question_type,
                                model=model_name
                            )
                            
                            sub_marks_awarded: int = sub_evaluation.marks_awarded
                            total_marks_obtained += sub_marks_awarded
                            total_marks_possible += sub_question_marks
                            
                            # Store remarks if points were cut
                            if sub_marks_awarded < sub_question_marks and sub_evaluation.remarks.strip():
                                remarks[sub_question_id] = sub_evaluation.remarks
                            
                            # Store results using QuestionResult model for type safety
                            sub_question_result = QuestionResult(
                                question_id=sub_question_id,
                                question_text=sub_question_text,
                                student_answer=sub_student_answer,
                                marks_awarded=sub_marks_awarded,
                                total_marks=sub_question_marks,
                                percentage=sub_evaluation.percentage,
                                justification=sub_evaluation.justification,
                                remarks=sub_evaluation.remarks
                            )
                            evaluation_results.append(sub_question_result.model_dump())
                        else:
                            # No answer provided for sub-question
                            total_marks_possible += sub_question_marks
                            remarks[sub_question_id] = "No answer provided"
                            
                            no_answer_result = QuestionResult(
                                question_id=sub_question_id,
                                question_text=sub_question_text,
                                student_answer="",
                                marks_awarded=0,
                                total_marks=sub_question_marks,
                                percentage=0,
                                justification="No answer provided",
                                remarks="No answer provided"
                            )
                            evaluation_results.append(no_answer_result.model_dump())
                else:
                    # No answer provided for main question
                    total_marks_possible += question_marks
                    remarks[question_id] = "No answer provided"
                    
                    no_answer_result = QuestionResult(
                        question_id=question_id,
                        question_text=question_text,
                        student_answer="",
                        marks_awarded=0,
                        total_marks=question_marks,
                        percentage=0,
                        justification="No answer provided",
                        remarks="No answer provided"
                    )
                    evaluation_results.append(no_answer_result.model_dump())
            
            # Calculate final percentage
            final_percentage: float = (total_marks_obtained / total_marks_possible) * 100 if total_marks_possible > 0 else 0
            
            # Save evaluation to database
            evaluation = Evaluation(
                student_id=student.id,
                question_bank_id=question_bank_id,
                total_marks_obtained=total_marks_obtained,
                total_marks_possible=total_marks_possible,
                percentage=final_percentage,
                answer_file_name=filename,
                parsed_answers_json=parsed_answers,
                evaluation_results_json=evaluation_results,
                remarks_json=remarks,
                processing_status="completed",
                completed_at=datetime.now(timezone.utc)
            )
            
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)
            
            # Return using Pydantic model
            return ProcessingResult(
                evaluation_id=evaluation.id,
                student_name=student_name,
                total_marks_obtained=total_marks_obtained,
                total_marks_possible=total_marks_possible,
                percentage=final_percentage,
                evaluation_results=evaluation_results,
                remarks=remarks,
                status="completed"
            )
            
        except Exception as e:
            print(f"Error processing answer sheet {filename}: {e}")
            student_name = self.document_parser.extract_student_name_from_filename(filename)
            return ProcessingResult(
                student_name=student_name,
                status="failed",
                error=str(e)
            )
        finally:
            if db is not None:
                db.close()
    
    def process_batch_answer_sheets(
        self,
        files: List[Tuple[bytes, str]],  # List of (file_content, filename) tuples
        question_bank_id: int,
        model_name: Optional[str] = None,
        batch_size: int = 32
    ) -> List[ProcessingResult]:
        """Process batch of answer sheets"""
        
        results: List[ProcessingResult] = []
        total_files: int = len(files)
        
        # Process in batches
        for i in range(0, total_files, batch_size):
            batch = files[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(total_files + batch_size - 1)//batch_size}")
            
            for file_content, filename in batch:
                result = self.process_single_answer_sheet(
                    file_content, filename, question_bank_id, model_name
                )
                results.append(result)
        
        return results


# Global evaluation engine instance
evaluation_engine = EvaluationEngine()
