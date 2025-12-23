# AutoDataFlow 🚀🕷️
**AI-Powered Web Scraping, Data Cleaning, and Analysis Platform**

AutoDataFlow is a modern, full-stack application that transforms the tedious process of web scraping into a streamlined, intelligent workflow. It combines robust browser automation (Playwright) with Generative AI (Gemini) to not just extract data, but clean, analyze, and visualize it automatically.

![Hero Image](https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80) 
*(Note: Replace with actual screenshot if available)*

---

## ✨ Features

### 1. 🕷️ Universal Web Scraping
- **Playwright Integration**: Handles dynamic JavaScript-heavy websites (SPAs) with ease.
- **Smart Table Extraction**: Automatically identifies and extracts `<table>` elements and converts them to structured data.
- **LLM Fallback**: If standard extraction fails, uses AI to parse unstructured text into tables.

### 2. 🧹 AI-Powered Data Cleaning
- **User-Directed Cleaning**: Simply tell the AI "Remove the dollar signs" or "Convert 'billions' to numbers", and it writes the code for you.
- **File-Specific Targeting**: Select specific tables within a job to clean without affecting others.
- **Auto-Fix**: The system attempts to self-correct generated code if it encounters errors (e.g., import issues).

### 3. 📊 AI Data Analyst
- **Natural Language Q&A**: Ask questions like "Who has the highest net worth?" and get instant answers based on your data.
- **Interactive Visualizations**: Ask "Make a bar chart of X vs Y" to generate interactive Plotly charts.
- **Robust Error Handling**: Friendly feedback when AI quotas are exceeded or data is malformed.

### 4. 💾 Flexible Export
- **Formats**: CSV, JSON (Zipped), Parquet, SQLite.
- **Robust Downloads**: Handles large datasets and prevents file locking issues on Windows.

---

## 🛠️ Tech Stack

### Backend (`/src`)
- **FastAPI**: High-performance async Python API.
- **Redis + RQ**: Reliable background task queue for scraping and long-running jobs.
- **Playwright**: Browser automation.
- **Pandas**: Data manipulation and cleaning.
- **LLM API**: Generative AI for cleaning and analysis.

### Frontend (`/frontend`)
- **Next.js 14**: React framework with App Router.
- **Shadcn UI**: Beautiful, accessible components.
- **Tailwind CSS**: Modern styling.
- **Framer Motion**: Smooth animations.
- **Plotly.js**: Interactive data visualization.

---

## 🚀 Quick Start (Docker)

The easiest way to run the entire stack is with Docker Compose.

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/AutoDataFlow.git
    cd AutoDataFlow
    ```

2.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```ini
    LLM_API_KEY=your_gemini_api_key_here
    REDIS_URL=redis://redis:6379/0
    ```

3.  **Run with Docker**:
    ```bash
    docker-compose up --build
    ```
    This will start:
    - Backend API at `http://localhost:8000`
    - Frontend App at `http://localhost:3000`
    - Redis
    - Worker process

---

## 🏃 Manual Setup (Local Dev)

If you prefer running without Docker:

### Backend
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Start Redis**: Ensure a Redis instance is running locally.
3.  **Start Worker**:
    ```bash
    python src/worker.py
    ```
4.  **Start API**:
    ```bash
    uvicorn src.main:app --reload
    ```

### Frontend
1.  **Navigate to frontend**:
    ```bash
    cd frontend
    ```
2.  **Install Node Modules**:
    ```bash
    npm install
    ```
3.  **Start Dev Server**:
    ```bash
    npm run dev
    ```
    Access the app at `http://localhost:3000`.

---

## 📖 How to Use

1.  **Create a Job**: Go to "New Job". Enter a URL (or prompt).
2.  **Scrape**: Wait for the system to crawl and extract tables.
3.  **Preview**: View the raw data in the Data Grid.
4.  **Clean (Optional)**:
    - Click "Auto-Clean".
    - Select a file.
    - Type instructions (e.g., "Remove null rows").
    - Result is saved as `cleaned_filename.csv`.
5.  **Analyze**: Use the AI Analyst chat to ask questions or generate charts.
6.  **Export**: Download your data in your preferred format.

---

## 📄 License
MIT License.