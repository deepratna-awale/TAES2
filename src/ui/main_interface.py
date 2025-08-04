"""
Main Gradio interface for TAES 2
"""

import gradio as gr
import json
from typing import List, Optional, Tuple
from src.database.models import QuestionBank, Student, Evaluation
from src.database.init_db import get_db
from src.llm.manager import llm_manager
from src.evaluation.engine import evaluation_engine
from src.parsing.document_parser import document_parser

def create_main_interface():
    """Create the main Gradio interface"""
    
    with gr.Blocks(title="T.E.A.S 2 - Theoretical Answer Evaluation System") as interface:
        gr.Markdown("# T.E.A.S 2 - Theoretical Answer Evaluation System")
        gr.Markdown("Automated answer evaluation using AI and RAG technology")
        
        with gr.Tabs():
            # Tab 1: Marking Criterion Setup
            with gr.TabItem("📋 Marking Criterion"):
                gr.Markdown("## Configure Marking Criterion")
                
                with gr.Row():
                    total_marks = gr.Number(
                        label="Total Marks",
                        value=100,
                        precision=0,
                        minimum=1
                    )
                    
                    mark_distribution = gr.Dropdown(
                        label="Mark Distribution",
                        choices=["in_paper", "uniform"],
                        value="in_paper",
                        info="Select how marks are distributed"
                    )
                
                per_question_marks = gr.Number(
                    label="Per Question Marks",
                    value=10,
                    precision=0,
                    minimum=1,
                    visible=False,
                    info="Only used for uniform distribution"
                )
                
                def update_per_question_visibility(distribution):
                    return gr.update(visible=(distribution == "uniform"))
                
                mark_distribution.change(
                    update_per_question_visibility,
                    inputs=[mark_distribution],
                    outputs=[per_question_marks]
                )
            
            # Tab 2: Question Bank Upload
            with gr.TabItem("📚 Question Bank"):
                gr.Markdown("## Upload Question Bank")
                
                question_bank_name = gr.Textbox(
                    label="Question Bank Name",
                    placeholder="Enter a name for this question bank"
                )
                
                question_bank_description = gr.Textbox(
                    label="Description (Optional)",
                    placeholder="Brief description of the question bank",
                    lines=3
                )
                
                question_file = gr.File(
                    label="Upload Question Bank",
                    file_types=[".pdf", ".docx", ".txt"],
                    file_count="single"
                )
                
                with gr.Row():
                    model_selection = gr.Dropdown(
                        label="LLM Model",
                        choices=[
                            "gpt-3.5-turbo",
                            "gpt-4",
                            "gpt-4-turbo",
                            "claude-3-sonnet",
                            "claude-3-haiku",
                            "gemini-pro",
                            "ollama/llama2",
                            "ollama/mistral"
                        ],
                        value="gpt-3.5-turbo"
                    )
                
                process_questions_btn = gr.Button("Process Question Bank", variant="primary")
                question_processing_output = gr.JSON(label="Processed Questions Preview")
                save_question_bank_btn = gr.Button("Save Question Bank", variant="secondary")
                question_bank_status = gr.Textbox(label="Status", interactive=False)
                
                def process_question_bank(name, description, file, total_marks_val, distribution, per_q_marks, model):
                    if not file or not name:
                        return None, "Please provide question bank name and file"
                    
                    try:
                        # Read file content
                        with open(file.name, 'rb') as f:
                            file_content = f.read()
                        
                        # Parse document
                        text_content = document_parser.parse_document(file_content, file.name)
                        
                        # Extract questions using LLM
                        questions_data = llm_manager.parse_questions_from_text(
                            text_content,
                            total_marks_val,
                            distribution,
                            per_q_marks if distribution == "uniform" else None,
                            model
                        )
                        
                        return questions_data, "Questions processed successfully! Review and then save."
                        
                    except Exception as e:
                        return None, f"Error processing questions: {str(e)}"
                
                def save_question_bank_to_db(name, description, questions_json, total_marks_val, distribution, per_q_marks):
                    if not questions_json or not name:
                        return "Please process questions first and provide a name"
                    
                    db = None
                    try:
                        db = next(get_db())
                        
                        question_bank = QuestionBank(
                            name=name,
                            description=description or "",
                            total_marks=int(total_marks_val),
                            mark_distribution=distribution,
                            per_question_marks=int(per_q_marks) if distribution == "uniform" else None,
                            questions_json=questions_json
                        )
                        
                        db.add(question_bank)
                        db.commit()
                        db.refresh(question_bank)
                        
                        return f"Question bank saved successfully with ID: {question_bank.id}"
                        
                    except Exception as e:
                        return f"Error saving question bank: {str(e)}"
                    finally:
                        if db is not None:
                            db.close()
                
                process_questions_btn.click(
                    process_question_bank,
                    inputs=[
                        question_bank_name, question_bank_description, question_file,
                        total_marks, mark_distribution, per_question_marks, model_selection
                    ],
                    outputs=[question_processing_output, question_bank_status]
                )
                
                save_question_bank_btn.click(
                    save_question_bank_to_db,
                    inputs=[
                        question_bank_name, question_bank_description, question_processing_output,
                        total_marks, mark_distribution, per_question_marks
                    ],
                    outputs=[question_bank_status]
                )
            
            # Tab 3: Single Answer Sheet
            with gr.TabItem("📝 Single Answer Sheet"):
                gr.Markdown("## Evaluate Single Answer Sheet")
                
                # Question bank selection
                question_bank_dropdown = gr.Dropdown(
                    label="Select Question Bank",
                    choices=[],
                    info="Choose the question bank to evaluate against"
                )
                
                refresh_qb_btn = gr.Button("Refresh Question Banks")
                
                def refresh_question_banks():
                    db = None
                    try:
                        db = next(get_db())
                        question_banks = db.query(QuestionBank).all()
                        choices = [(f"{qb.name} (ID: {qb.id})", qb.id) for qb in question_banks]
                        return gr.update(choices=choices)
                    except Exception as e:
                        print(f"Error refreshing question banks: {e}")
                        return gr.update(choices=[])
                    finally:
                        if db is not None:
                            db.close()
                
                refresh_qb_btn.click(
                    refresh_question_banks,
                    outputs=[question_bank_dropdown]
                )
                
                # File upload
                single_answer_file = gr.File(
                    label="Upload Answer Sheet",
                    file_types=[".pdf", ".docx"],
                    file_count="single"
                )
                
                single_model_selection = gr.Dropdown(
                    label="LLM Model",
                    choices=[
                        "gpt-3.5-turbo",
                        "gpt-4",
                        "gpt-4-turbo",
                        "claude-3-sonnet",
                        "claude-3-haiku",
                        "gemini-pro",
                        "ollama/llama2",
                        "ollama/mistral"
                    ],
                    value="gpt-3.5-turbo"
                )
                
                evaluate_single_btn = gr.Button("Evaluate Answer Sheet", variant="primary")
                single_evaluation_output = gr.JSON(label="Evaluation Results")
                single_status = gr.Textbox(label="Status", interactive=False)
                
                def evaluate_single_answer(question_bank_id, file, model):
                    if not file or not question_bank_id:
                        return None, "Please select question bank and upload answer sheet"
                    
                    try:
                        # Read file content
                        with open(file.name, 'rb') as f:
                            file_content = f.read()
                        
                        # Process answer sheet
                        result = evaluation_engine.process_single_answer_sheet(
                            file_content, file.name, question_bank_id, model
                        )
                        
                        if result.status == "completed":
                            return result.model_dump(), f"Evaluation completed! Student: {result.student_name}, Score: {result.percentage:.1f}%"
                        else:
                            error_msg = result.error if result.error else "Unknown error"
                            return result.model_dump(), f"Evaluation failed: {error_msg}"
                        
                    except Exception as e:
                        return None, f"Error during evaluation: {str(e)}"
                
                evaluate_single_btn.click(
                    evaluate_single_answer,
                    inputs=[question_bank_dropdown, single_answer_file, single_model_selection],
                    outputs=[single_evaluation_output, single_status]
                )
            
            # Tab 4: Batch Processing
            with gr.TabItem("📋 Batch Processing"):
                gr.Markdown("## Batch Answer Sheet Evaluation")
                gr.Markdown("Upload up to 100 answer sheets for batch processing")
                
                batch_question_bank_dropdown = gr.Dropdown(
                    label="Select Question Bank",
                    choices=[],
                    info="Choose the question bank to evaluate against"
                )
                
                batch_refresh_qb_btn = gr.Button("Refresh Question Banks")
                batch_refresh_qb_btn.click(
                    refresh_question_banks,
                    outputs=[batch_question_bank_dropdown]
                )
                
                batch_answer_files = gr.File(
                    label="Upload Answer Sheets",
                    file_types=[".pdf", ".docx"],
                    file_count="multiple"
                )
                
                batch_model_selection = gr.Dropdown(
                    label="LLM Model",
                    choices=[
                        "gpt-3.5-turbo",
                        "gpt-4",
                        "gpt-4-turbo",
                        "claude-3-sonnet",
                        "claude-3-haiku",
                        "gemini-pro",
                        "ollama/llama2",
                        "ollama/mistral"
                    ],
                    value="gpt-3.5-turbo"
                )
                
                batch_size_input = gr.Number(
                    label="Batch Size",
                    value=32,
                    minimum=1,
                    maximum=100,
                    precision=0
                )
                
                evaluate_batch_btn = gr.Button("Start Batch Evaluation", variant="primary")
                batch_evaluation_output = gr.JSON(label="Batch Results Summary")
                batch_status = gr.Textbox(label="Status", interactive=False)
                
                def evaluate_batch_answers(question_bank_id, files, model, batch_size):
                    if not files or not question_bank_id:
                        return None, "Please select question bank and upload answer sheets"
                    
                    if len(files) > 100:
                        return None, "Maximum 100 files allowed for batch processing"
                    
                    try:
                        # Prepare file contents
                        file_data = []
                        for file in files:
                            with open(file.name, 'rb') as f:
                                file_content = f.read()
                            file_data.append((file_content, file.name))
                        
                        # Process batch
                        results = evaluation_engine.process_batch_answer_sheets(
                            file_data, question_bank_id, model, int(batch_size)
                        )
                        
                        # Create summary
                        completed = sum(1 for r in results if r.status == "completed")
                        failed = len(results) - completed
                        avg_score = sum(r.percentage or 0 for r in results if r.status == "completed") / completed if completed > 0 else 0
                        
                        summary = {
                            "total_files": len(results),
                            "completed": completed,
                            "failed": failed,
                            "average_score": avg_score,
                            "results": [r.model_dump() for r in results]
                        }
                        
                        return summary, f"Batch processing completed! {completed}/{len(results)} files processed successfully. Average score: {avg_score:.1f}%"
                        
                    except Exception as e:
                        return None, f"Error during batch evaluation: {str(e)}"
                
                evaluate_batch_btn.click(
                    evaluate_batch_answers,
                    inputs=[batch_question_bank_dropdown, batch_answer_files, batch_model_selection, batch_size_input],
                    outputs=[batch_evaluation_output, batch_status]
                )
            
            # Tab 5: Results & Analytics
            with gr.TabItem("📊 Results & Analytics"):
                gr.Markdown("## View Results and Analytics")
                
                with gr.Row():
                    student_search = gr.Textbox(
                        label="Search Student",
                        placeholder="Enter student name to search"
                    )
                    
                    search_btn = gr.Button("Search", variant="secondary")
                
                results_display = gr.Dataframe(
                    headers=["Student", "Question Bank", "Score (%)", "Total Marks", "Date", "Remarks"],
                    interactive=False
                )
                
                def search_student_results(student_name):
                    db = None
                    try:
                        db = next(get_db())
                        
                        if student_name:
                            # Search for specific student
                            students = db.query(Student).filter(Student.name.ilike(f"%{student_name}%")).all()
                        else:
                            # Get all students
                            students = db.query(Student).limit(50).all()
                        
                        results_data = []
                        for student in students:
                            for evaluation in student.evaluations:
                                question_bank = db.query(QuestionBank).filter(QuestionBank.id == evaluation.question_bank_id).first()
                                
                                # Count remarks
                                remarks_count = len(evaluation.remarks_json or {})
                                remarks_text = f"{remarks_count} remarks" if remarks_count > 0 else "No remarks"
                                
                                results_data.append([
                                    student.name,
                                    question_bank.name if question_bank else "Unknown",
                                    f"{evaluation.percentage:.1f}",
                                    f"{evaluation.total_marks_obtained}/{evaluation.total_marks_possible}",
                                    evaluation.created_at.strftime("%Y-%m-%d %H:%M"),
                                    remarks_text
                                ])
                        
                        return results_data
                        
                    except Exception as e:
                        print(f"Error searching results: {e}")
                        return []
                    finally:
                        if db is not None:
                            db.close()
                
                search_btn.click(
                    search_student_results,
                    inputs=[student_search],
                    outputs=[results_display]
                )
                
                # Load initial data
                interface.load(
                    search_student_results,
                    inputs=[gr.Textbox(value="", visible=False)],
                    outputs=[results_display]
                )
    
    return interface
