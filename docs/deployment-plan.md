# Zomato Recommendation System - Deployment Plan

This document outlines the steps required to deploy the FastAPI backend to Railway and the Next.js frontend to Vercel.

## 1. Backend Deployment (Railway)

We will use Railway to host the FastAPI Python backend. Railway automatically detects Python applications via the `requirements.txt` file.

### Prerequisites
- Create a [Railway account](https://railway.app/).
- Connect your GitHub repository to Railway.

### Deployment Steps
1. **Create a New Project**: In your Railway dashboard, click **New Project** and select **Deploy from GitHub repo**.
2. **Select Repository**: Choose your Zomato project repository.
3. **Configure the Start Command**:
   By default, Railway might try to infer how to run the app. Go to the **Settings** tab of your service, under **Build / Deploy**, and ensure the **Start Command** is set to:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```
4. **Environment Variables**:
   Go to the **Variables** tab in Railway and add the environment variables from your `.env` file. Do not commit your actual `.env` file to GitHub.
   - `GROQ_API_KEY`: *(Paste your Groq API Key here)*
   - `GROQ_MODEL`: `llama-3.3-70b-versatile`
   - `GROQ_FALLBACK_MODEL`: `llama-3.1-8b-instant`
   - `GROQ_TEMPERATURE`: `0.3`
   - `HF_DATASET_NAME`: `ManikaSaini/zomato-restaurant-recommendation`
   - `MAX_CANDIDATES_FOR_LLM`: `20`
   - `TOP_K_RECOMMENDATIONS`: `5`
5. **Deploy**: Railway will trigger a build and deploy the backend. Wait for it to finish and note the generated **public domain/URL**.

> [!WARNING]
> After deploying the frontend, you will need to come back to the backend code and update the CORS settings in `src/main.py` to allow the Vercel URL.

---

## 2. Frontend Deployment (Vercel)

We will use Vercel to host the Next.js frontend. Vercel provides seamless integration with Next.js applications.

### Prerequisites
- Create a [Vercel account](https://vercel.com/).
- Connect your GitHub account to Vercel.

### Deployment Steps
1. **Create a New Project**: In the Vercel dashboard, click **Add New** -> **Project**.
2. **Import Repository**: Select your Zomato project repository.
3. **Configure Project Settings**:
   - **Framework Preset**: Vercel should automatically detect `Next.js`.
   - **Root Directory**: Click **Edit** and select the `frontend` folder (since your Next.js app is inside the `frontend` directory).
4. **Environment Variables**:
   Expand the **Environment Variables** section and add the following:
   - `NEXT_PUBLIC_API_BASE_URL`: The URL of your deployed Railway backend (e.g., `https://your-backend.up.railway.app`). Ensure there is no trailing slash.
5. **Deploy**: Click **Deploy**. Vercel will build and deploy your frontend. Once complete, it will provide a public URL (e.g., `https://your-frontend.vercel.app`).

---

## 3. Post-Deployment (CORS Update)

Once both the backend and frontend are deployed, you need to update the backend to allow requests from the deployed frontend.

1. Open `src/main.py`.
2. Locate the CORS middleware configuration and add your new Vercel URL:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:3000",   # Next.js default
           "http://localhost:5173",   # Vite default
           "https://your-frontend.vercel.app" # <-- ADD YOUR VERCEL URL HERE
       ],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```
3. Commit and push the changes. Railway will automatically redeploy the backend with the updated CORS settings.

Your application is now fully deployed and communicating securely!
