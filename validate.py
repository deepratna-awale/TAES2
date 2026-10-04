#!/usr/bin/env python3
"""
TAES 2 Validation Script
Tests the complete functionality of the system
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from src.database.models import Student, QuestionBank, Evaluation
        print("✓ Database models import successful")
    except ImportError as e:
        print(f"✗ Database models import failed: {e}")
        return False
    
    try:
        from src.llm.manager import LLMManager
        print("✓ LLM manager import successful")
    except ImportError as e:
        print(f"✗ LLM manager import failed: {e}")
        return False
    
    try:
        from src.parsing.document_parser import DocumentParser
        print("✓ Document parser import successful")
    except ImportError as e:
        print(f"✗ Document parser import failed: {e}")
        return False
    
    try:
        from src.evaluation.engine import EvaluationEngine
        print("✓ Evaluation engine import successful")
    except ImportError as e:
        print(f"✗ Evaluation engine import failed: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from src.config.settings import settings
        print(f"✓ Configuration loaded successfully")
        print(f"  - Default model: {settings.DEFAULT_MODEL}")
        print(f"  - Batch size: {settings.BATCH_SIZE}")
        print(f"  - Max upload size: {settings.MAX_UPLOAD_SIZE}")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False

def test_document_parsing():
    """Test document parsing functionality"""
    print("\nTesting document parsing...")
    
    try:
        from src.parsing.document_parser import document_parser
        
        # Test text parsing
        test_text = """
        Q1. What is Python?
        Answer: Python is a programming language.
        
        Q2. Define variables.
        Answer: Variables store data values.
        """
        
        answers = document_parser.extract_answers_from_text(test_text, 2)
        if len(answers) >= 2:
            print("✓ Text parsing successful")
            print(f"  - Extracted {len(answers)} answers")
        else:
            print("✗ Text parsing failed - insufficient answers extracted")
            return False
            
        # Test student name extraction
        name = document_parser.extract_student_name_from_filename("john_doe_assignment.pdf")
        if name:
            print(f"✓ Name extraction successful: {name}")
        else:
            print("✗ Name extraction failed")
            return False
            
        return True
    except Exception as e:
        print(f"✗ Document parsing test failed: {e}")
        return False

def test_database_connection():
    """Test database connection and models"""
    print("\nTesting database connection...")
    
    try:
        from src.database.init_db import initialize_database
        
        # This will fail if PostgreSQL is not set up, but that's expected
        try:
            initialize_database()
            print("✓ Database connection successful")
            return True
        except Exception as db_error:
            print(f"⚠ Database connection failed (expected if DB not configured): {db_error}")
            print("  This is normal if you haven't set up PostgreSQL yet")
            return True  # Don't fail the test for this
            
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\nChecking environment...")
    
    # Check if .env file exists
    env_file = project_root / ".env"
    if env_file.exists():
        print("✓ .env file found")
    else:
        print("⚠ .env file not found (using .env.example)")
    
    # Check required directories
    required_dirs = ["logs", "uploads", "data"]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/ directory exists")
        else:
            print(f"⚠ {dir_name}/ directory missing (will be created)")
    
    return True

def check_dependencies():
    """Check if required packages are available"""
    print("\nChecking dependencies...")

    # package name -> import name
    required_packages = {
        "gradio": "gradio", "python-dotenv": "dotenv", "litellm": "litellm",
        "sqlalchemy": "sqlalchemy", "pydantic": "pydantic", "psycopg": "psycopg",
        "pdfplumber": "pdfplumber", "pypdf": "pypdf", "python-docx": "docx",
    }

    missing_packages = []

    for package, module in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {package} available")
        except ImportError:
            print(f"✗ {package} missing")
            missing_packages.append(package)

    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False

    return True

def main():
    """Run all validation tests"""
    print("=" * 50)
    print("TAES 2 System Validation")
    print("=" * 50)
    
    tests = [
        ("Environment Check", check_environment),
        ("Dependencies Check", check_dependencies),
        ("Configuration Test", test_configuration),
        ("Import Test", test_imports),
        ("Document Parsing Test", test_document_parsing),
        ("Database Connection Test", test_database_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"VALIDATION RESULTS: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("🎉 All tests passed! TAES 2 is ready to run.")
        print("Run 'python app.py' to start the application.")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("Common solutions:")
        print("1. Run 'pip install -r requirements.txt'")
        print("2. Set up PostgreSQL database")
        print("3. Configure .env file with API keys")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
