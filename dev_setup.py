"""
Development utilities and testing helpers
"""

import os
import tempfile
from typing import Dict, Any
from src.utils.test_data import get_sample_data
from src.database.init_db import initialize_database, get_db
from src.database.models import QuestionBank, Student

def create_test_files():
    """Create test files for development"""
    sample_data = get_sample_data()
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="taes2_test_")
    
    # Create question paper file
    question_file = os.path.join(temp_dir, "sample_questions.txt")
    with open(question_file, 'w', encoding='utf-8') as f:
        f.write(sample_data["question_paper"])
    
    # Create answer sheet files
    answer_files = []
    for answer in sample_data["answer_sheets"]:
        answer_file = os.path.join(temp_dir, answer["name"])
        with open(answer_file, 'w', encoding='utf-8') as f:
            f.write(answer["content"])
        answer_files.append(answer_file)
    
    return {
        "temp_dir": temp_dir,
        "question_file": question_file,
        "answer_files": answer_files
    }

def setup_test_database():
    """Set up test database with sample data"""
    try:
        # Initialize database
        initialize_database()
        
        # Create sample question bank
        db = next(get_db())
        
        sample_questions = {
            "questions": [
                {
                    "id": "Q1",
                    "text": "Define the following terms with examples:",
                    "type": "define",
                    "marks": 10,
                    "sub_questions": [
                        {"id": "Q1a", "text": "Function", "type": "define", "marks": 5},
                        {"id": "Q1b", "text": "Domain and Range", "type": "define", "marks": 5}
                    ]
                },
                {
                    "id": "Q2",
                    "text": "Solve the following equations:",
                    "type": "solve",
                    "marks": 20,
                    "sub_questions": [
                        {"id": "Q2a", "text": "2x + 5 = 15", "type": "solve", "marks": 10},
                        {"id": "Q2b", "text": "x² - 4x + 4 = 0", "type": "solve", "marks": 10}
                    ]
                },
                {
                    "id": "Q3",
                    "text": "Explain the concept of limits in calculus with at least two examples.",
                    "type": "explain",
                    "marks": 25,
                    "sub_questions": []
                },
                {
                    "id": "Q4",
                    "text": "Prove that the sum of first n natural numbers is n(n+1)/2.",
                    "type": "prove",
                    "marks": 20,
                    "sub_questions": []
                },
                {
                    "id": "Q5",
                    "text": "Short answer questions:",
                    "type": "short",
                    "marks": 25,
                    "sub_questions": [
                        {"id": "Q5a", "text": "What is the derivative of sin(x)?", "type": "short", "marks": 5},
                        {"id": "Q5b", "text": "State the fundamental theorem of calculus.", "type": "short", "marks": 10},
                        {"id": "Q5c", "text": "Define continuity of a function.", "type": "define", "marks": 10}
                    ]
                }
            ],
            "total_marks": 100,
            "question_count": 5
        }
        
        question_bank = QuestionBank(
            name="Sample Mathematics Final Exam",
            description="Sample question bank for testing TAES 2 functionality",
            total_marks=100,
            mark_distribution="in_paper",
            questions_json=sample_questions
        )
        
        db.add(question_bank)
        db.commit()
        db.refresh(question_bank)
        
        print(f"Test question bank created with ID: {question_bank.id}")
        return question_bank.id
        
    except Exception as e:
        print(f"Error setting up test database: {e}")
        return None
    finally:
        db.close()

def cleanup_test_files(temp_dir: str):
    """Clean up test files"""
    import shutil
    try:
        shutil.rmtree(temp_dir)
        print(f"Cleaned up test directory: {temp_dir}")
    except Exception as e:
        print(f"Error cleaning up test files: {e}")

if __name__ == "__main__":
    # Run development setup
    print("Setting up TAES 2 development environment...")
    
    # Setup test database
    qb_id = setup_test_database()
    
    # Create test files
    test_files = create_test_files()
    
    print("\nDevelopment setup completed!")
    print(f"Test question bank ID: {qb_id}")
    print(f"Test files directory: {test_files['temp_dir']}")
    print(f"Question file: {test_files['question_file']}")
    print(f"Answer files: {test_files['answer_files']}")
    print("\nYou can now run 'python app.py' to start the application.")
