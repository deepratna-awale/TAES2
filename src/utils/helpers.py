"""
Utility functions for TAES 2
"""

import re
import hashlib
from typing import List, Dict, Any, Optional

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\'\"]+', '', text)
    
    return text.strip()

def extract_question_number(text: str) -> Optional[int]:
    """Extract question number from text"""
    patterns = [
        r'^(\d+)[\.\)]\s*',
        r'^Q(\d+)[\.\)]\s*',
        r'^Question\s*(\d+)[\.\)]\s*'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None

def generate_file_hash(content: bytes) -> str:
    """Generate hash for file content to detect duplicates"""
    return hashlib.md5(content).hexdigest()

def validate_file_type(filename: str, allowed_extensions: set) -> bool:
    """Validate if file type is allowed"""
    if not filename:
        return False
    
    file_extension = '.' + filename.lower().split('.')[-1]
    return file_extension in allowed_extensions

def format_marks_display(marks_obtained: float, total_marks: float) -> str:
    """Format marks for display"""
    percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
    return f"{marks_obtained:.1f}/{total_marks:.1f} ({percentage:.1f}%)"

def calculate_grade(percentage: float) -> str:
    """Calculate letter grade based on percentage"""
    if percentage >= 90:
        return "A+"
    elif percentage >= 85:
        return "A"
    elif percentage >= 80:
        return "A-"
    elif percentage >= 75:
        return "B+"
    elif percentage >= 70:
        return "B"
    elif percentage >= 65:
        return "B-"
    elif percentage >= 60:
        return "C+"
    elif percentage >= 55:
        return "C"
    elif percentage >= 50:
        return "C-"
    elif percentage >= 45:
        return "D"
    else:
        return "F"

def split_into_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Split a list into batches of specified size"""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches

def create_evaluation_summary(evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create summary statistics from evaluation results"""
    if not evaluations:
        return {
            "total_evaluations": 0,
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "pass_rate": 0,
            "grade_distribution": {}
        }
    
    completed_evaluations = [e for e in evaluations if e.get("status") == "completed"]
    
    if not completed_evaluations:
        return {
            "total_evaluations": len(evaluations),
            "completed": 0,
            "failed": len(evaluations),
            "average_score": 0,
            "highest_score": 0,
            "lowest_score": 0,
            "pass_rate": 0,
            "grade_distribution": {}
        }
    
    scores = [e["percentage"] for e in completed_evaluations]
    
    # Calculate statistics
    average_score = sum(scores) / len(scores)
    highest_score = max(scores)
    lowest_score = min(scores)
    pass_rate = (len([s for s in scores if s >= 50]) / len(scores)) * 100
    
    # Grade distribution
    grades = [calculate_grade(score) for score in scores]
    grade_distribution = {}
    for grade in set(grades):
        grade_distribution[grade] = grades.count(grade)
    
    return {
        "total_evaluations": len(evaluations),
        "completed": len(completed_evaluations),
        "failed": len(evaluations) - len(completed_evaluations),
        "average_score": average_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "pass_rate": pass_rate,
        "grade_distribution": grade_distribution
    }
