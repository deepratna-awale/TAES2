"""
LLM Integration using LiteLLM for multiple model support
"""

import os
import json
from typing import Dict, List, Optional, Any 
from litellm import completion
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationInfo

load_dotenv()


class LLMMessage(BaseModel):
    """Type-safe message structure for LLM communication"""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {'system', 'user', 'assistant'}
        if v not in valid_roles:
            raise ValueError(f"Role must be one of {valid_roles}")
        return v


class EvaluationResult(BaseModel):
    """Type-safe evaluation result from LLM"""
    marks_awarded: int = Field(..., ge=0, description="Marks awarded to the answer")
    total_marks: int = Field(..., gt=0, description="Total marks possible")
    percentage: float = Field(..., ge=0, le=100, description="Percentage score")
    justification: str = Field(..., description="Brief explanation of the evaluation")
    remarks: str = Field(default="", description="Specific feedback if points were deducted")
    
    @field_validator('marks_awarded')
    @classmethod
    def validate_marks_awarded(cls, v: int, info: ValidationInfo) -> int:
        if hasattr(info, 'data') and info.data and 'total_marks' in info.data:
            total = info.data['total_marks']
            if isinstance(total, int) and v > total:
                raise ValueError("Marks awarded cannot exceed total marks")
        return v


class SubQuestion(BaseModel):
    """Type-safe sub-question structure"""
    id: str = Field(..., description="Sub-question identifier")
    text: str = Field(..., description="Sub-question text")
    type: str = Field(..., description="Question type")
    marks: int = Field(..., gt=0, description="Marks for this sub-question")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {'explain', 'define', 'short', 'long', 'calculate', 'analyze'}
        if v not in valid_types:
            raise ValueError(f"Question type must be one of {valid_types}")
        return v


class ParsedQuestion(BaseModel):
    """Type-safe parsed question structure"""
    id: str = Field(..., description="Question identifier")
    text: str = Field(..., description="Question text")
    type: str = Field(..., description="Question type")
    marks: int = Field(..., gt=0, description="Marks for this question")
    sub_questions: List[SubQuestion] = Field(default_factory=list, description="Sub-questions")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {'explain', 'define', 'short', 'long', 'calculate', 'analyze'}
        if v not in valid_types:
            raise ValueError(f"Question type must be one of {valid_types}")
        return v


class QuestionParseResult(BaseModel):
    """Type-safe question parsing result"""
    questions: List[ParsedQuestion] = Field(..., description="Parsed questions")
    total_marks: int = Field(..., gt=0, description="Total marks for all questions")
    question_count: int = Field(..., gt=0, description="Number of questions")
    
    @field_validator('question_count')
    @classmethod
    def validate_question_count(cls, v: int, info: ValidationInfo) -> int:
        if hasattr(info, 'data') and info.data and 'questions' in info.data:
            questions = info.data['questions']
            if isinstance(questions, list) and v != len(questions):
                raise ValueError("Question count must match actual number of questions")
        return v


class LLMManager:
    """Manages LLM interactions with support for multiple providers"""
    
    def __init__(self) -> None:
        self.default_model: str = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
        self.default_temperature: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
        self.default_max_tokens: int = int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))
        
        # Set up API keys for different providers
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            os.environ["OPENAI_API_KEY"] = openai_key
            
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
            
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            os.environ["GEMINI_API_KEY"] = gemini_key
    
    def get_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Get completion from specified LLM model"""
        
        try:
            response = completion(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                **kwargs
            )
            
            # Handle the response properly with type safety
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    content = choice.message.content
                    return content if content is not None else ""
            
            raise ValueError("Invalid response format from LLM")
            
        except Exception as e:
            print(f"Error getting LLM completion: {e}")
            raise
    
    def evaluate_answer(
        self,
        question: str,
        student_answer: str,
        reference_answer: Optional[str] = None,
        marks: int = 10,
        question_type: str = "explain",
        model: Optional[str] = None
    ) -> EvaluationResult:
        """Evaluate a student answer against a question"""
        
        # Construct evaluation prompt
        system_prompt = """You are an expert academic evaluator. Your task is to evaluate student answers fairly and provide constructive feedback.

Guidelines:
1. Award marks based on correctness, completeness, and clarity
2. Consider the question type (define, explain, short answer, long answer)
3. Provide specific feedback on what was done well and what could be improved
4. If points are deducted, explain why clearly
5. Be consistent and fair in your evaluation"""

        user_prompt = f"""
Question: {question}
Question Type: {question_type}
Total Marks: {marks}

Student Answer:
{student_answer}

{f"Reference Answer: {reference_answer}" if reference_answer else ""}

Please evaluate this answer and provide:
1. Marks awarded (out of {marks})
2. Brief justification for the marks
3. Specific remarks ONLY if points were deducted (what was missing or incorrect)

Respond in the following JSON format:
{{
    "marks_awarded": <number>,
    "total_marks": {marks},
    "percentage": <percentage>,
    "justification": "<brief explanation>",
    "remarks": "<specific feedback only if points were cut, otherwise empty string>"
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = ""
        try:
            response = self.get_completion(messages, model=model)
            
            # Parse JSON response
            result_dict = json.loads(response)
            
            # Validate and convert to Pydantic model
            result = EvaluationResult(**result_dict)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Raw response: {response}")
            raise
        except Exception as e:
            print(f"Error in answer evaluation: {e}")
            raise
    
    def parse_questions_from_text(
        self,
        question_text: str,
        total_marks: int,
        mark_distribution: str,
        per_question_marks: Optional[int] = None,
        model: Optional[str] = None
    ) -> QuestionParseResult:
        """Parse questions from uploaded question bank text"""
        
        system_prompt = """You are an expert at parsing academic question papers. Extract questions, sub-questions, and their marks from the given text."""

        user_prompt = f"""
Please parse the following question paper text and extract all questions and sub-questions with their marks.

Question Paper Text:
{question_text}

Total Marks: {total_marks}
Mark Distribution: {mark_distribution}
{"Per Question Marks: " + str(per_question_marks) if per_question_marks else ""}

Instructions:
1. Identify all questions (Q1, Q2, 1., 2., etc.)
2. Identify sub-questions (a), b), i), ii), etc.)
3. Extract marks for each question/sub-question
4. Determine question types (define, explain, short answer, long answer, etc.)

Respond in the following JSON format:
{{
    "questions": [
        {{
            "id": "Q1",
            "text": "Question text",
            "type": "explain|define|short|long",
            "marks": <number>,
            "sub_questions": [
                {{
                    "id": "Q1a",
                    "text": "Sub-question text",
                    "type": "explain|define|short|long",
                    "marks": <number>
                }}
            ]
        }}
    ],
    "total_marks": {total_marks},
    "question_count": <number>
}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = ""
        try:
            response = self.get_completion(messages, model=model)
            
            # Parse JSON response
            result_dict = json.loads(response)
            
            # Validate and convert to Pydantic model
            result = QuestionParseResult(**result_dict)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing question extraction response as JSON: {e}")
            print(f"Raw response: {response}")
            raise
        except Exception as e:
            print(f"Error in question parsing: {e}")
            raise


# Global LLM manager instance
llm_manager = LLMManager()
