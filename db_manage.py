#!/usr/bin/env python3
"""
TAES 2 Database Management Utility
Provides database operations and maintenance tools
"""

import sys
import os
from pathlib import Path
import argparse
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def init_database() -> bool:
    """Initialize database tables"""
    try:
        from src.database.init_db import initialize_database
        print("Initializing database tables...")
        initialize_database()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def check_connection() -> bool:
    """Check database connection"""
    try:
        from src.database.init_db import get_db
        db: Session = next(get_db())
        print("✅ Database connection successful!")
        
        # Test a simple query
        result = db.execute(text("SELECT version();")).fetchone()
        if result:
            print(f"PostgreSQL version: {result[0]}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_sample_data() -> bool:
    """Create sample data for testing"""
    try:
        from dev_setup import setup_test_database
        print("Creating sample question bank...")
        qb_id: Optional[int] = setup_test_database()
        if qb_id is not None:
            print(f"✅ Sample question bank created with ID: {qb_id}")
            return True
        else:
            print("❌ Failed to create sample data")
            return False
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def backup_database() -> bool:
    """Create database backup"""
    try:
        from src.config.settings import settings
        import subprocess
        
        # Parse database URL
        db_url: str = settings.DATABASE_URL
        if not db_url.startswith('postgresql://'):
            print("❌ Only PostgreSQL databases are supported for backup")
            return False
        
        # Extract connection details
        # postgresql://user:password@host:port/database
        url_parts = db_url.replace('postgresql://', '').split('@')
        user_pass = url_parts[0].split(':')
        host_port_db = url_parts[1].split('/')
        host_port = host_port_db[0].split(':')
        
        user: str = user_pass[0]
        password: str = user_pass[1] if len(user_pass) > 1 else ''
        host: str = host_port[0]
        port: str = host_port[1] if len(host_port) > 1 else '5432'
        database: str = host_port_db[1]
        
        # Create backup filename
        timestamp: str = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file: str = f"taes2_backup_{timestamp}.sql"
        
        # Create backup command
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', database,
            '-f', backup_file,
            '--verbose'
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        print(f"Creating backup: {backup_file}")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database backup created: {backup_file}")
            return True
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False

def show_stats() -> bool:
    """Show database statistics"""
    try:
        from src.database.init_db import get_db
        from src.database.models import Student, QuestionBank, Evaluation
        
        db: Session = next(get_db())
        
        # Count records
        student_count: int = db.query(Student).count()
        question_bank_count: int = db.query(QuestionBank).count()
        evaluation_count: int = db.query(Evaluation).count()
        
        print("📊 Database Statistics:")
        print(f"  Students: {student_count}")
        print(f"  Question Banks: {question_bank_count}")
        print(f"  Evaluations: {evaluation_count}")
        
        if evaluation_count > 0:
            # Calculate average score
            evaluations = db.query(Evaluation).all()
            # Extract percentage values properly
            percentages = [float(e.percentage) for e in evaluations if hasattr(e, 'percentage')]
            if percentages:
                avg_score: float = sum(percentages) / len(percentages)
                print(f"  Average Score: {avg_score:.1f}%")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return False

def reset_database() -> bool:
    """Reset database (WARNING: Deletes all data)"""
    try:
        response: str = input("⚠️  WARNING: This will delete ALL data! Type 'CONFIRM' to proceed: ")
        if response != 'CONFIRM':
            print("Operation cancelled.")
            return False
        
        from src.database.init_db import engine
        from src.database.models import Base
        
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        
        print("Recreating tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database reset completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def main() -> None:
    parser = argparse.ArgumentParser(description='TAES 2 Database Management')
    parser.add_argument('command', choices=[
        'init', 'check', 'sample', 'backup', 'stats', 'reset'
    ], help='Database operation to perform')
    
    args = parser.parse_args()
    
    print("🗄️  TAES 2 Database Management")
    print("=" * 40)
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment loaded")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment")
    
    success: bool = False
    
    if args.command == 'init':
        success = init_database()
    elif args.command == 'check':
        success = check_connection()
    elif args.command == 'sample':
        success = create_sample_data()
    elif args.command == 'backup':
        success = backup_database()
    elif args.command == 'stats':
        success = show_stats()
    elif args.command == 'reset':
        success = reset_database()
    
    print("=" * 40)
    if success:
        print("✅ Operation completed successfully!")
    else:
        print("❌ Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
