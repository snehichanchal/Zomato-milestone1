# AI-Powered Zomato Restaurant Recommendation System

This project is an AI-powered restaurant recommendation service built using **Next.js** for the frontend, **FastAPI** for the backend, and the **Groq LLM (LLaMA 3.3)** for intelligent, context-aware reasoning. It filters restaurants from a curated dataset and provides ranked, personalized recommendations along with generated explanations based on user preferences.

## 🚀 Features

- **Dynamic Frontend:** Built with Next.js and React, offering a modern, sleek UI.
- **FastAPI Backend:** A lightweight, high-performance Python backend serving API endpoints.
- **AI-Powered Recommendations:** Integrates with Groq API (LLaMA 3.3 70B) to rank restaurants and provide reasoning tailored to the user's preferences.
- **Dataset Integration:** Uses the Hugging Face `ManikaSaini/zomato-restaurant-recommendation` dataset for structured queries.
- **Smart Filtering:** Deterministic pre-filtering based on location, budget, and rating to prevent LLM hallucination and reduce token costs.
- **CLI Mode:** Includes `predict.py` for headless execution and quick testing.

## 🛠️ Technology Stack

- **Frontend:** Next.js, React, Vanilla CSS
- **Backend:** Python 3.11+, FastAPI, Uvicorn
- **AI / LLM:** Groq API (`llama-3.3-70b-versatile`)
- **Data Handling:** pandas, Hugging Face `datasets`

## 📦 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.11+)
- Groq API Key

### Backend Setup
1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables:
   Copy `.env.example` to `.env` (or create one) and add your Groq API key:
   ```env
   GROQ_API_KEY="your_groq_api_key_here"
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn src.main:app --reload
   ```

### Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📁 Project Structure

- `/src`: Backend API routes, services, data models, and prompt builder.
- `/frontend`: Next.js frontend application and components.
- `/data`: Cached datasets (auto-generated).
- `/docs`: Architecture and implementation details.
- `predict.py`: CLI testing tool.

## 📝 License
This project is for educational purposes.
