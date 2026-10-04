"""
LLM Integration using LiteLLM for multiple model support
"""

import os
import re
import json
from typing import Dict, List, Optional, Any 
from litellm import completion
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationInfo

load_dotenv()

VALID_QUESTION_TYPES = {'explain', 'define', 'short', 'long', 'calculate', 'analyze', 'solve', 'prove'}


def normalize_question_type(value: Any) -> str:
    """Map whatever the LLM returned to a known question type, defaulting to 'explain'"""
    text = str(value or "").strip().lower()
    for candidate in re.split(r"[|/,\s]+", text):
        if candidate in VALID_QUESTION_TYPES:
            return candidate
    return "explain"


def extract_json(response: str) -> Dict[str, Any]:
    """Parse a JSON object out of an LLM response.

    Models often wrap JSON in markdown fences or add a sentence around it.
    """
    text = (response or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


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
    marks_awarded: float = Field(..., ge=0, description="Marks awarded to the answer")
    total_marks: float = Field(..., gt=0, description="Total marks possible")
    percentage: float = Field(default=0, ge=0, le=100, description="Percentage score")
    justification: str = Field(default="", description="Brief explanation of the evaluation")
    remarks: str = Field(default="", description="Specific feedback if points were deducted")
    
    @model_validator(mode="before")
    @classmethod
    def clamp_and_compute(cls, data: Any) -> Any:
        """Keep marks within [0, total] and derive the percentage from them"""
        if isinstance(data, dict):
            data = dict(data)
            try:
                total = float(data.get("total_marks") or 0)
                awarded = float(data.get("marks_awarded") or 0)
            except (TypeError, ValueError):
                return data
            if total > 0:
                awarded = max(0.0, min(awarded, total))
                data["marks_awarded"] = awarded
                data["percentage"] = round(awarded / total * 100, 2)
            for key in ("justification", "remarks"):
                if data.get(key) is None:
                    data[key] = ""
        return data


class SubQuestion(BaseModel):
    """Type-safe sub-question structure"""
    id: str = Field(..., description="Sub-question identifier")
    text: str = Field(..., description="Sub-question text")
    type: str = Field(default="explain", description="Question type")
    marks: float = Field(default=0, ge=0, description="Marks for this sub-question")
    
    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v: Any) -> str:
        return normalize_question_type(v)


class ParsedQuestion(BaseModel):
    """Type-safe parsed question structure"""
    id: str = Field(..., description="Question identifier")
    text: str = Field(..., description="Question text")
    type: str = Field(default="explain", description="Question type")
    marks: float = Field(default=0, ge=0, description="Marks for this question")
    sub_questions: List[SubQuestion] = Field(default_factory=list, description="Sub-questions")
    
    @field_validator('type', mode='before')
    @classmethod
    def validate_type(cls, v: Any) -> str:
        return normalize_question_type(v)


class QuestionParseResult(BaseModel):
    """Type-safe question parsing result"""
    questions: List[ParsedQuestion] = Field(..., min_length=1, description="Parsed questions")
    total_marks: float = Field(..., gt=0, description="Total marks for all questions")
    question_count: int = Field(default=0, ge=0, description="Number of questions")
    
    @model_validator(mode="after")
    def sync_question_count(self) -> "QuestionParseResult":
        # The count is derived, so trust the actual list over the model's arithmetic
        self.question_count = len(self.questions)
        return self


class LLMManager:
    """Manages LLM interactions with support for multiple providers"""
    
    def __init__(self) -> None:
        self.default_model: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
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
        
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def get_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """Get completion from specified LLM model"""
        
        model_name = model or self.default_model
        if model_name.startswith(("ollama/", "ollama_chat/")):
            kwargs.setdefault("api_base", self.ollama_base_url)
        
        try:
            response = completion(
                model=model_name,
                messages=messages,
                temperature=self.default_temperature if temperature is None else temperature,
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
        marks: float = 10,
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

        reference_section = ""
        if reference_answer:
            reference_section = (
                "Reference material provided by the teacher (use it as the marking guide; give credit "
                "for correct points phrased differently, and do not penalise correct points it does not "
                "mention):\n" + reference_answer + "\n"
            )

        user_prompt = f"""
Question: {question}
Question Type: {question_type}
Total Marks: {marks}

Student Answer:
{student_answer}

{reference_section}

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
            result_dict = extract_json(response)
            # The question's marks are authoritative, not what the model echoes back
            result_dict["total_marks"] = marks
            
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
        total_marks: float,
        mark_distribution: str,
        per_question_marks: Optional[float] = None,
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
            result_dict = extract_json(response)
            result_dict.setdefault("total_marks", total_marks)
            
            # With uniform distribution every main question carries the same marks
            if mark_distribution == "uniform" and per_question_marks:
                for question in result_dict.get("questions", []):
                    question["marks"] = per_question_marks
            
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
