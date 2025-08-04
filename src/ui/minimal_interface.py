"""
Minimal Gradio interface for TAES 2
A simplified interface for basic evaluation tasks
"""

import gradio as gr
from typing import Optional
from src.database.models import QuestionBank
from src.database.init_db import get_db
from src.evaluation.engine import evaluation_engine


def create_minimal_interface():
    """Create a minimal Gradio interface for basic evaluation"""
    
    with gr.Blocks(title="T.E.A.S 2 - Minimal Interface") as interface:
        gr.Markdown("# T.E.A.S 2 - Minimal Interface")
        gr.Markdown("Quick answer evaluation with minimal setup")
        
        with gr.Row():
            with gr.Column(scale=2):
                # Question bank selection
                question_bank_dropdown = gr.Dropdown(
                    label="Select Question Bank",
                    choices=[],
                    info="Choose the question bank to evaluate against"
                )
                
                refresh_btn = gr.Button("🔄 Refresh")
                
                # File upload
                answer_file = gr.File(
                    label="Upload Answer Sheet",
                    file_types=[".pdf", ".docx"],
                    file_count="single"
                )
                
                # Model selection
                model_selection = gr.Dropdown(
                    label="AI Model",
                    choices=[
                        "gpt-3.5-turbo",
                        "gpt-4",
                        "claude-3-haiku",
                        "gemini-pro"
                    ],
                    value="gpt-3.5-turbo"
                )
                
                evaluate_btn = gr.Button("📊 Evaluate", variant="primary")
            
            with gr.Column(scale=3):
                # Results display
                status_output = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=2
                )
                
                score_output = gr.HTML(
                    label="Score",
                    value="<div style='text-align: center; font-size: 24px; color: #666;'>No evaluation yet</div>"
                )
                
                details_output = gr.JSON(
                    label="Detailed Results",
                    visible=False
                )
                
                show_details_btn = gr.Button("Show Details", variant="secondary", visible=False)
        
        def refresh_question_banks():
            """Refresh the question banks dropdown"""
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
        
        def evaluate_answer(question_bank_id, file, model):
            """Evaluate a single answer sheet"""
            if not file or not question_bank_id:
                return (
                    "❌ Please select a question bank and upload an answer sheet",
                    "<div style='text-align: center; font-size: 24px; color: #f56565;'>No evaluation</div>",
                    None,
                    gr.update(visible=False)
                )
            
            try:
                # Read file content
                with open(file.name, 'rb') as f:
                    file_content = f.read()
                
                # Process answer sheet
                result = evaluation_engine.process_single_answer_sheet(
                    file_content, file.name, question_bank_id, model
                )
                
                if result.status == "completed":
                    # Format score display
                    score_html = f"""
                    <div style='text-align: center; padding: 20px; border-radius: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;'>
                        <div style='font-size: 32px; font-weight: bold; margin-bottom: 10px;'>{result.percentage:.1f}%</div>
                        <div style='font-size: 16px; opacity: 0.9;'>
                            {result.total_marks_obtained}/{result.total_marks_possible} marks
                        </div>
                        <div style='font-size: 14px; opacity: 0.8; margin-top: 10px;'>
                            Student: {result.student_name}
                        </div>
                    </div>
                    """
                    
                    status_msg = f"✅ Evaluation completed successfully!\nStudent: {result.student_name}\nProcessed {len(result.evaluation_results or [])} questions"
                    
                    return (
                        status_msg,
                        score_html,
                        result.model_dump(),
                        gr.update(visible=True)
                    )
                else:
                    error_msg = result.error if result.error else "Unknown error"
                    return (
                        f"❌ Evaluation failed: {error_msg}",
                        "<div style='text-align: center; font-size: 24px; color: #f56565;'>Failed</div>",
                        result.model_dump(),
                        gr.update(visible=False)
                    )
                    
            except Exception as e:
                return (
                    f"❌ Error during evaluation: {str(e)}",
                    "<div style='text-align: center; font-size: 24px; color: #f56565;'>Error</div>",
                    None,
                    gr.update(visible=False)
                )
        
        def toggle_details(details_data):
            """Toggle the visibility of detailed results"""
            if details_data:
                return gr.update(visible=True)
            return gr.update(visible=False)
        
        # Event handlers
        refresh_btn.click(
            refresh_question_banks,
            outputs=[question_bank_dropdown]
        )
        
        evaluate_btn.click(
            evaluate_answer,
            inputs=[question_bank_dropdown, answer_file, model_selection],
            outputs=[status_output, score_output, details_output, show_details_btn]
        )
        
        show_details_btn.click(
            toggle_details,
            inputs=[details_output],
            outputs=[details_output]
        )
        
        # Load initial data
        interface.load(
            refresh_question_banks,
            outputs=[question_bank_dropdown]
        )
    
    return interface
