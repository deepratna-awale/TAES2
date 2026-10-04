# T.E.A.S 2 - Theoretical Answer Evaluation System

An addition to T.A.E.S: Automatically evaluate theoretical answers using SOTA LLM and RAG technology.

## Features

### 🎯 Core Functionality
- **Automated Answer Evaluation**: Uses state-of-the-art LLMs to evaluate student answers
- **Multi-LLM Support**: Compatible with GPT, Claude, Gemini, and local models via Ollama
- **Multiple Interface Modes**: Choose from Main (full-featured), Minimal (basic), or Simple (user-friendly) interfaces
- **Question Bank Management**: Upload and parse question papers from PDF/DOCX files
- **Batch Processing**: Evaluate up to 100 answer sheets simultaneously
- **Smart Answer Detection**: Automatically detects and maps answer numbers
- **Detailed Feedback**: Provides specific remarks only when marks are deducted

### 📊 Marking System
- **Flexible Mark Distribution**: Choose between paper-based or uniform marking
- **Configurable Criteria**: Set total marks and per-question marks
- **Detailed Analytics**: View student performance and grade distributions
- **Comprehensive Reports**: Track individual student progress and remarks

### 🖥️ User Interface Options
- **Main Interface**: Full-featured interface with all capabilities including batch processing and analytics
- **Simple Interface**: Streamlined, user-friendly interface perfect for general use
- **Minimal Interface**: Basic interface for quick evaluation tasks

### 🗄️ Database & Storage
- **PostgreSQL Integration**: Robust database with proper relationships
- **Student Management**: Track student information and evaluation history
- **Vector Storage**: Built-in vector store for advanced RAG capabilities
- **Evaluation History**: Complete audit trail of all evaluations

## Installation

### Prerequisites
- Python 3.10 or higher
- PostgreSQL database (or Docker for easy setup)
- API keys for chosen LLM providers

### Quick Setup

1. **Clone the repository**
```bash
git clone https://github.com/deepratna-awale/TAES2.git
cd TAES2
```

2. **Choose your setup method**

**Option A: Docker Setup (Recommended)**
```bash
cp .env.example .env      # then add an LLM API key and a POSTGRES_PASSWORD
docker compose up -d --build

# View logs
docker compose logs -f app

# Access the application at http://localhost:7860
```

**Option B: Manual Setup**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Or use the convenient startup script
chmod +x start.sh
./start.sh help
```

3. **Configure environment variables**
Copy and edit the environment file:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Key environment variables:
```env
# Interface Mode (main, minimal, simple)
TAES_INTERFACE_MODE=simple

# Server Configuration
TAES_SERVER_NAME=0.0.0.0
TAES_SERVER_PORT=7860
TAES_DEBUG=false

# Optional login for the web UI
TAES_AUTH_USERNAME=teacher
TAES_AUTH_PASSWORD=

# Database Configuration (only needed outside Docker)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/taes2_db

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Default LLM Settings (any LiteLLM model name)
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=2000
```

4. **Start the application**

**With startup script:**
```bash
# Start with simple interface (recommended for first-time users)
./start.sh start simple

# Start with main interface (full features)
./start.sh start main

# Start with minimal interface (basic features)
./start.sh start minimal

# Run tests
./start.sh test

# Start with Docker
./start.sh docker
```

**Or directly with Python:**
```bash
# Set interface mode and start
export TAES_INTERFACE_MODE=simple
python app.py

# Or pass interface mode as argument
python app.py simple
```

5. **Access the application**
- **Main Application**: http://localhost:7860
- **Database Admin** (if using Docker): http://localhost:8080

## Usage Guide

### Interface Modes

TAES 2 offers three interface modes to suit different user needs:

#### 🎯 Main Interface (Full-Featured)
- Complete question bank management with CRUD operations
- Batch processing for up to 100 answer sheets
- Advanced analytics and results dashboard
- Comprehensive student management
- Best for: Educational institutions, power users

#### 🎨 Simple Interface (User-Friendly)
- Streamlined design with grouped controls
- Enhanced score visualization with color coding
- Quick statistics and expandable detailed results
- Better error handling and user feedback
- Best for: Teachers, general users

#### ⚡ Minimal Interface (Basic)
- Clean, distraction-free interface
- Essential evaluation features only
- Quick file upload and evaluation
- Compact results display
- Best for: Quick evaluations, simple tasks

### Getting Started

1. **Choose Your Interface Mode**
Set the interface mode in your `.env` file or use the startup script:
```bash
# Using environment variable
export TAES_INTERFACE_MODE=simple

# Using startup script
./start.sh start simple
```

2. **Configure Marking Criterion** (Main Interface Only)
- Set total marks for the evaluation
- Choose mark distribution method:
  - **In Paper**: Marks are specified in the question paper
  - **Uniform Distribution**: Equal marks for all questions

3. **Upload Question Bank**
- Upload your question paper (PDF/DOCX format)
- The system will automatically parse questions and sub-questions
- Review the extracted questions and save the question bank

4. **Evaluate Answer Sheets**

#### Single Answer Sheet (All Interfaces)
- Select a question bank
- Upload a student's answer sheet
- Get instant evaluation results with detailed feedback

#### Batch Processing (Main Interface Only)
- Upload up to 100 answer sheets
- Process them in configurable batch sizes
- View comprehensive results and analytics

5. **View Results & Analytics**
- Search for specific students
- View evaluation history
- Analyze performance trends
- Export results for further analysis

## Startup Script Commands

The included `start.sh` script provides convenient commands for managing the application:

```bash
# Start the application with different interfaces
./start.sh start main     # Full-featured interface
./start.sh start simple   # User-friendly interface  
./start.sh start minimal  # Basic interface

# Docker operations
./start.sh docker         # Start with existing Docker images
./start.sh docker-build   # Rebuild and start with Docker
./start.sh clean          # Clean up Docker containers and volumes

# Testing and validation
./start.sh test           # Run application tests
./start.sh help           # Show all available commands
```

## Troubleshooting

### Common Issues

1. **LLM errors during evaluation**
   - Check the API key for the provider of the model you picked
   - Model names follow LiteLLM, e.g. `gpt-4o-mini`, `anthropic/claude-3-5-haiku-latest`, `gemini/gemini-2.0-flash`, `ollama/llama3`

2. **Database Connection Issues**
   - Check your `DATABASE_URL` in `.env`
   - Ensure PostgreSQL is running
   - For Docker: `docker compose logs database`

3. **Missing Dependencies**
   - Run: `pip install -r requirements.txt`
   - Or use the startup script: `./start.sh test`

4. **Interface Not Loading**
   - Check the console for error messages
   - Verify all environment variables are set
   - Try a different interface mode: `export TAES_INTERFACE_MODE=minimal`

### Log Files
Check the following locations for detailed error information:
- Application logs: `logs/` directory
- Docker logs: `docker compose logs app`
- Database logs: `docker compose logs database`

## Database Management

TAES 2 includes a comprehensive database management utility:

```bash
# Check database connection
python db_manage.py check

# Initialize database tables
python db_manage.py init

# Create sample data for testing
python db_manage.py sample

# View database statistics
python db_manage.py stats

# Create database backup
python db_manage.py backup

# Reset database (WARNING: Deletes all data)
python db_manage.py reset
```


## Environment Variables

All environment variables are documented in `.env.example`. Key variables include:

### Interface Configuration
- `TAES_INTERFACE_MODE`: Choose interface mode (main, minimal, simple)
- `TAES_SERVER_NAME`: Server host (default: 0.0.0.0)
- `TAES_SERVER_PORT`: Server port (default: 7860)
- `TAES_DEBUG`: Enable debug mode (true/false)
- `TAES_SHARE_GRADIO`: Create public Gradio link (true/false)

### Database Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: alternative to `DATABASE_URL`
- `DB_CONNECT_RETRIES`: how many times to wait for the database at startup (default 10)

### Access Control
- `TAES_AUTH_USERNAME` / `TAES_AUTH_PASSWORD`: require a login for the web UI when both are set

### LLM Configuration  
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key
- `GEMINI_API_KEY`: Google Gemini API key
- `OLLAMA_BASE_URL`: Ollama server URL
- `DEFAULT_MODEL`: Default LLM model to use
- `MODEL_CHOICES`: Comma separated models offered in the UI
- `DEFAULT_TEMPERATURE`: Default temperature setting
- `DEFAULT_MAX_TOKENS`: Default maximum tokens

## LLM Provider Support

Any model [LiteLLM](https://docs.litellm.ai/docs/providers) supports works; set the list shown in the UI with `MODEL_CHOICES`.

### Cloud Providers
- **OpenAI**: e.g. `gpt-4o-mini`, `gpt-4o`
- **Anthropic**: e.g. `anthropic/claude-3-5-haiku-latest`
- **Google**: e.g. `gemini/gemini-2.0-flash`

### Local Models
- **Ollama**: e.g. `ollama/llama3`, `ollama/mistral` (server at `OLLAMA_BASE_URL`)

## Project Structure

```
TAES2/
├── app.py                          # Main application entry point
├── start.sh                       # Convenient startup script
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Test dependencies
├── docker-compose.yml             # Local Docker stack (app + Postgres)
├── Dockerfile                     # Application Docker image
├── .env.example                   # Environment variables template
├── tests/                         # Pytest suite
├── src/
│   ├── config/
│   │   └── settings.py            # Application configuration
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models
│   │   └── init_db.py             # Database initialization
│   ├── llm/
│   │   └── manager.py             # LLM integration manager
│   ├── parsing/
│   │   └── document_parser.py     # Document parsing utilities
│   ├── evaluation/
│   │   └── engine.py              # Main evaluation engine
│   ├── ui/
│   │   ├── main_interface.py      # Full-featured Gradio interface
│   │   ├── simple_interface.py    # User-friendly interface
│   │   ├── minimal_interface.py   # Basic interface
│   │   ├── common.py              # Shared UI helpers
│   │   └── __init__.py            # UI package exports
│   ├── schemas/
│   │   └── models.py              # Pydantic schemas
│   └── utils/
│       ├── helpers.py             # Utility functions
│       ├── logging_config.py      # Logging configuration
│       └── test_data.py           # Test data generation
├── logs/                          # Application logs
├── uploads/                       # Uploaded files
└── data/                          # Data storage
```

## Supported File Formats

- **Question Papers**: PDF, DOCX, TXT
- **Answer Sheets**: PDF, DOCX, TXT

Scanned (image only) PDFs and legacy `.doc` files are not supported.

## Docker Deployment

The application includes a complete Docker setup with PostgreSQL database:

```bash
cp .env.example .env            # set POSTGRES_PASSWORD and an LLM key

# Build and start all services
docker compose up -d --build

# View application logs
docker compose logs -f app

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: Deletes data)
docker compose down --volumes
```

### Docker Services
- **app**: Main TAES 2 application (port 7860)
- **database**: PostgreSQL 16 (port 5432, bound to localhost only)
- **pgadmin**: Database administration interface (port 8080), optional: `docker compose --profile admin up -d`

## Testing

```bash
pip install -r requirements-dev.txt
pytest -q tests

# Against PostgreSQL instead of SQLite
TEST_DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/taes2_db pytest -q tests
```

## Database Schema

### Tables
- **students**: Student information and contact details
- **question_banks**: Question papers and marking schemes
- **evaluations**: Evaluation results and detailed feedback
- **vector_store**: Vector embeddings for RAG functionality

## API Integration

The system uses [LiteLLM](https://github.com/BerriAI/litellm) for unified LLM integration, allowing easy switching between different providers without code changes.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the GNU GPL v3 - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the logs in the `logs/` directory

## References
T.A.E.S: https://www.researchgate.net/publication/370215129_Monograph_on_Theoretical_Answer_Evaluation_System



