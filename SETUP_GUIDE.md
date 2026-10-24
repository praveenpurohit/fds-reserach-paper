# 🚀 AcademicRAG — Quick Setup & Run Guide

A step-by-step guide to set up and run this project from scratch on macOS, Linux, or Windows (WSL).

---

## 📋 Prerequisites

Before starting, make sure you have:
1. **Python 3.10, 3.11, or 3.12** installed (`python3 --version`).
2. **Git** installed.
3. *(Recommended)* **Ollama** installed for running models locally and privately for free.
   - Download & install from: [https://ollama.com](https://ollama.com)

---

## ⚡ Quick Start (Automated - Mac/Linux)

If you are on macOS or Linux, you can simply run:

```bash
chmod +x run.sh
./run.sh
```

This script will automatically:
- Create a virtual environment (`venv`).
- Install all dependencies.
- Verify Ollama connectivity.
- Launch the web app at [http://localhost:8501](http://localhost:8501).

---

## 🛠️ Step-by-Step Manual Setup (Recommended for Full Control)

### 1. Clone & Enter the Directory
```bash
git clone <repository-url>
cd AcademicRAG
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate

# On Windows (cmd.exe):
# .venv\Scripts\activate.bat
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

1. Create a `.env` file from the provided example:
   ```bash
   cp .env.example .env
   ```

2. Open `.env` and verify the settings:
   ```ini
   # Ollama settings (Local, free, private)
   OLLAMA_MODEL=qwen2.5:3b
   OLLAMA_BASE_URL=http://localhost:11434

   # (Optional) Claude API Key - only if you prefer using Anthropic Claude API
   ANTHROPIC_API_KEY=

   # Application settings
   APP_TITLE=AcademicRAG
   TOP_K_RESULTS=5
   ```

---

## 🤖 Starting Ollama (Local AI Model)

If you plan to use Ollama for free, local inference:

1. **Start the Ollama server** (in a separate terminal window or as a background app):
   ```bash
   ollama serve
   ```
   *(On macOS, you can also just open the Ollama desktop app).*

2. **Pull the model configured in your `.env`**:
   ```bash
   ollama pull qwen2.5:3b
   ```
   *(Or if you want Llama 3.1: `ollama pull llama3.1:8b` and update `OLLAMA_MODEL` in `.env`)*.

---

## 🏃 Running the Application

Make sure your virtual environment is activated (`source .venv/bin/activate`), then launch Streamlit:

```bash
streamlit run app/main.py
```

Open your browser and navigate to:
👉 **`http://localhost:8501`**

---

## 📚 How to Use AcademicRAG

1. **Add / Upload Papers**:
   - In the sidebar, use the **Upload Research Paper (PDF)** uploader to add PDF files, then click **Index Uploaded Papers**.
   - Or place PDF files in the `papers/` directory and run:
     ```bash
     python add_paper.py papers/your_paper.pdf
     ```
2. **Select Analysis Scope**:
   - You can chat across all papers or choose a specific document from the **Active Analysis Scope** dropdown.
3. **Ask Questions**:
   - Query literature reviews, ask for methodology summaries, compare claims, or extract citations.
4. **Choose LLM Backend**:
   - **Ollama (Local)**: Completely offline and free.
   - **Claude API**: Requires `ANTHROPIC_API_KEY` set in `.env`.
   - **Claude Code CLI**: If you use Anthropic's Claude Code CLI.

---

## ❓ Common Troubleshooting

- **`bad interpreter: /bin/bash^M` when running `./run.sh`**:
  - Run `sed -i '' -e 's/\r$//' run.sh` (macOS) or `dos2unix run.sh` to remove Windows CRLF line endings.
- **Port 8501 already in use**:
  - Kill existing processes: `pkill -f streamlit` or run on another port:
    ```bash
    streamlit run app/main.py --server.port 8502
    ```
- **ChromaDB / Collection not found error**:
  - Ensure only one instance of Streamlit is running.
  - In the sidebar, click the **Reindex** button to refresh the embeddings.
- **Ollama connection error**:
  - Verify Ollama is running by opening [http://localhost:11434](http://localhost:11434) in your browser or running `curl http://localhost:11434`.
