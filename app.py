"""
TAES 2 - Theoretical Answer Evaluation System
Main application entry point
"""
import os
import sys
from dotenv import load_dotenv

from src.ui.main_interface import create_main_interface
from src.ui.minimal_interface import create_minimal_interface
from src.ui.simple_interface import create_simple_interface
from src.database.init_db import initialize_database

# Load environment variables
load_dotenv()

def get_interface_mode() -> str:
    """Get the interface mode from environment variable or command line argument"""
    # Check environment variable first
    mode = os.getenv("TAES_INTERFACE_MODE", "main").lower()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        arg_mode = sys.argv[1].lower()
        if arg_mode in ["main", "minimal", "simple"]:
            mode = arg_mode
    
    return mode

def create_gradio_app():
    """Create and return the Gradio interface"""
    try:
        # Initialize database
        print("Initializing database...")
        initialize_database()
        print("Database initialized successfully!")
        
        # Get interface mode
        interface_mode = get_interface_mode()
        print(f"Starting TAES 2 with '{interface_mode}' interface...")
        
        # Create the appropriate Gradio interface
        if interface_mode == "minimal":
            interface = create_minimal_interface()
        elif interface_mode == "simple":
            interface = create_simple_interface()
        else:  # default to main
            interface = create_main_interface()
        
        print(f"Interface '{interface_mode}' created successfully!")
        return interface
        
    except Exception as e:
        print(f"Error creating application: {e}")
        # Return a basic error interface
        import gradio as gr
        with gr.Blocks(title="TAES 2 - Error") as error_interface:
            gr.Markdown(f"""
            # ❌ TAES 2 - Application Error
            
            **Error occurred during application startup:**
            
            ```
            {str(e)}
            ```
            
            Please check:
            1. Database connection settings
            2. Required dependencies are installed
            3. Environment variables are configured properly
            
            See the console output for more details.
            """)
        return error_interface

def main():
    """Launch the application directly"""
    
    try:
        # Create the Gradio interface
        interface = create_gradio_app()
        
        # Get configuration from environment
        server_name = os.getenv("TAES_SERVER_NAME", "0.0.0.0")
        server_port = int(os.getenv("TAES_SERVER_PORT", "7860"))
        share_gradio = os.getenv("TAES_SHARE_GRADIO", "false").lower() == "true"
        debug_mode = os.getenv("TAES_DEBUG", "true").lower() == "true"
        
        print(f"Launching on {server_name}:{server_port}")
        print(f"Share: {share_gradio}, Debug: {debug_mode}")
        
        # Launch the application using Gradio's built-in server
        interface.launch(
            share=share_gradio,
            server_name=server_name,
            server_port=server_port,
            debug=debug_mode,
            show_error=True,
            quiet=False
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error launching application: {e}")
        sys.exit(1)

# For backwards compatibility, create an app variable
# but now it's just for reference, not ASGI
app = None

if __name__ == "__main__":
    print("🚀 Starting TAES 2 - Theoretical Answer Evaluation System")
    print("Available interface modes: main, minimal, simple")
    print("Usage: python app.py [interface_mode]")
    print("Environment variables: TAES_INTERFACE_MODE, TAES_SERVER_NAME, TAES_SERVER_PORT, TAES_SHARE_GRADIO, TAES_DEBUG")
    print("-" * 80)
    main()
