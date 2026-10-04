"""
Simple Gradio interface for TAES 2
A streamlined interface for quick evaluations without complex features
"""

import html
import gradio as gr
from typing import Optional, List
from src.evaluation.engine import evaluation_engine
from src.ui.common import MODEL_CHOICES, DEFAULT_MODEL, read_upload, refresh_question_banks_update


def create_simple_interface():
    """Create a simple Gradio interface for straightforward evaluation"""
    
    with gr.Blocks(title="T.E.A.S 2 - Simple Interface") as interface:
        # Header
        with gr.Row():
            gr.Markdown(
                """
                # 📚 T.E.A.S 2 - Simple Interface
                ## Quick and Easy Answer Evaluation
                Upload your answer sheet and get instant AI-powered evaluation results.
                """,
                elem_id="header"
            )
        
        with gr.Row():
            # Left column - Input controls
            with gr.Column(scale=1, min_width=300):
                gr.Markdown("### 🔧 Configuration")
                
                # Question bank selection
                with gr.Group():
                    question_bank_dropdown = gr.Dropdown(
                        label="📋 Question Bank",
                        choices=[],
                        info="Select the question bank for evaluation"
                    )
                    
                    refresh_btn = gr.Button(
                        "🔄 Refresh Question Banks",
                        variant="secondary"
                    )
                
                # File upload
                with gr.Group():
                    answer_file = gr.File(
                        label="📄 Answer Sheet",
                        file_types=[".pdf", ".docx", ".txt"],
                        file_count="single"
                    )
                
                # AI model selection
                with gr.Group():
                    model_selection = gr.Dropdown(
                        label="🤖 AI Model",
                        choices=MODEL_CHOICES,
                        value=DEFAULT_MODEL,
                        info="Choose the AI model for evaluation"
                    )
                
                # Evaluation button
                evaluate_btn = gr.Button(
                    "🚀 Start Evaluation",
                    variant="primary"
                )
            
            # Right column - Results
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Results")
                
                # Status indicator
                status_output = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=3,
                    max_lines=5
                )
                
                # Score display
                with gr.Group():
                    score_display = gr.HTML(
                        value="""
                        <div style='text-align: center; padding: 40px; border: 2px dashed #ccc; border-radius: 10px; background-color: #f9f9f9;'>
                            <div style='font-size: 20px; color: #666; margin-bottom: 10px;'>📋</div>
                            <div style='font-size: 16px; color: #888;'>Upload an answer sheet to see results</div>
                        </div>
                        """
                    )
                
                # Expandable detailed results
                with gr.Accordion("📝 Detailed Results", open=False, visible=False) as details_accordion:
                    detailed_results = gr.JSON(
                        label="Evaluation Details",
                        show_label=False
                    )
                
                # Quick statistics
                with gr.Group(visible=False) as stats_group:
                    gr.Markdown("### 📈 Quick Stats")
                    with gr.Row():
                        total_questions = gr.Number(
                            label="Total Questions",
                            interactive=False,
                            precision=0
                        )
                        answered_questions = gr.Number(
                            label="Answered",
                            interactive=False,
                            precision=0
                        )
                        avg_score_per_question = gr.Number(
                            label="Avg Score/Question (%)",
                            interactive=False,
                            precision=1
                        )
        
        def refresh_question_banks():
            """Refresh the question banks dropdown"""
            return refresh_question_banks_update("{name} ({total_marks} marks)")
        
        def evaluate_answer_sheet(question_bank_id, file, model):
            """Evaluate the uploaded answer sheet"""
            if not file:
                return (
                    "⚠️ Please upload an answer sheet",
                    """
                    <div style='text-align: center; padding: 40px; border: 2px dashed #ff6b6b; border-radius: 10px; background-color: #ffe0e0;'>
                        <div style='font-size: 20px; color: #ff6b6b; margin-bottom: 10px;'>❌</div>
                        <div style='font-size: 16px; color: #cc5555;'>No file uploaded</div>
                    </div>
                    """,
                    None,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    0, 0, 0
                )
            
            if not question_bank_id:
                return (
                    "⚠️ Please select a question bank",
                    """
                    <div style='text-align: center; padding: 40px; border: 2px dashed #ff6b6b; border-radius: 10px; background-color: #ffe0e0;'>
                        <div style='font-size: 20px; color: #ff6b6b; margin-bottom: 10px;'>❌</div>
                        <div style='font-size: 16px; color: #cc5555;'>No question bank selected</div>
                    </div>
                    """,
                    None,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    0, 0, 0
                )
            
            try:
                # Update status to show processing
                processing_status = "🔄 Processing answer sheet...\nThis may take a few moments."
                
                # Read file content
                file_content, file_name = read_upload(file)
                
                # Process answer sheet
                result = evaluation_engine.process_single_answer_sheet(
                    file_content, file_name, question_bank_id, model
                )
                
                if result.status == "completed":
                    # Create success score display
                    percentage = result.percentage or 0
                    score_color = "#4CAF50" if percentage >= 70 else "#FF9800" if percentage >= 50 else "#F44336"
                    
                    score_html = f"""
                    <div style='text-align: center; padding: 30px; border-radius: 15px; background: linear-gradient(135deg, {score_color}15 0%, {score_color}25 100%); border: 2px solid {score_color}40;'>
                        <div style='font-size: 48px; font-weight: bold; color: {score_color}; margin-bottom: 15px;'>{percentage:.1f}%</div>
                        <div style='font-size: 18px; color: #333; margin-bottom: 10px;'>
                            <strong>{result.total_marks_obtained}</strong> out of <strong>{result.total_marks_possible}</strong> marks
                        </div>
                        <div style='font-size: 14px; color: #666; background: white; padding: 8px 16px; border-radius: 20px; display: inline-block;'>
                            Student: {html.escape(result.student_name)}
                        </div>
                    </div>
                    """
                    
                    # Calculate statistics
                    evaluation_results = result.evaluation_results or []
                    total_q = len(evaluation_results)
                    answered_q = len([r for r in evaluation_results if r.get("student_answer", "").strip()])
                    avg_score = (
                        sum(r.get("percentage", 0) for r in evaluation_results) / total_q
                        if total_q > 0 else 0
                    )
                    
                    status_msg = f"✅ Evaluation completed successfully!\n📋 Student: {result.student_name}\n📊 Processed {total_q} questions\n⏱️ Evaluation finished"
                    
                    return (
                        status_msg,
                        score_html,
                        result.model_dump(),
                        gr.update(visible=True),
                        gr.update(visible=True),
                        total_q,
                        answered_q,
                        avg_score
                    )
                else:
                    # Handle failure
                    error_msg = result.error if result.error else "Unknown error occurred"
                    
                    error_html = """
                    <div style='text-align: center; padding: 40px; border: 2px solid #f44336; border-radius: 10px; background-color: #ffebee;'>
                        <div style='font-size: 20px; color: #f44336; margin-bottom: 10px;'>❌</div>
                        <div style='font-size: 16px; color: #c62828;'>Evaluation Failed</div>
                    </div>
                    """
                    
                    return (
                        f"❌ Evaluation failed: {error_msg}",
                        error_html,
                        result.model_dump() if hasattr(result, 'model_dump') else None,
                        gr.update(visible=False),
                        gr.update(visible=False),
                        0, 0, 0
                    )
                    
            except Exception as e:
                error_html = f"""
                <div style='text-align: center; padding: 40px; border: 2px solid #f44336; border-radius: 10px; background-color: #ffebee;'>
                    <div style='font-size: 20px; color: #f44336; margin-bottom: 10px;'>⚠️</div>
                    <div style='font-size: 16px; color: #c62828;'>System Error</div>
                    <div style='font-size: 12px; color: #999; margin-top: 10px;'>{html.escape(str(e)[:100])}...</div>
                </div>
                """
                
                return (
                    f"❌ System error: {str(e)}",
                    error_html,
                    None,
                    gr.update(visible=False),
                    gr.update(visible=False),
                    0, 0, 0
                )
        
        # Event handlers
        refresh_btn.click(
            refresh_question_banks,
            outputs=[question_bank_dropdown]
        )
        
        evaluate_btn.click(
            evaluate_answer_sheet,
            inputs=[question_bank_dropdown, answer_file, model_selection],
            outputs=[
                status_output,
                score_display,
                detailed_results,
                details_accordion,
                stats_group,
                total_questions,
                answered_questions,
                avg_score_per_question
            ]
        )
        
        # Load initial data on interface start
        interface.load(
            refresh_question_banks,
            outputs=[question_bank_dropdown]
        )
    
    return interface
