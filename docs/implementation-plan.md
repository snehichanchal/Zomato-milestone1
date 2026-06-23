# Implementation Plan: AI-Powered Restaurant Recommendation System

This document outlines the phase-wise implementation strategy for the Zomato-inspired restaurant recommendation service, based on the architecture detailed in `architecture.md` and the requirements in `context.md`.

## Phase 1: Project Setup & Data Ingestion
**Goal:** Establish the project foundation, retrieve the dataset from Hugging Face, preprocess it, and provide a queryable in-memory repository.

### Tasks:
1. **Initialize Project Repository**
   - Create the directory structure: `src/data`, `src/models`, `src/services`, `src/api`, `src/ui`, `tests/`, and `data/`.
   - Setup `requirements.txt` with dependencies (`datasets`, `pandas`, `groq`, `pydantic`, `python-dotenv`, `streamlit`, `pytest`).
   - Create `.env.example` and `src/config.py` for configuration management.

2. **Implement Data Models**
   - Create `src/models/restaurant.py` to define the canonical `Restaurant` dataclass.

3. **Implement Dataset Loader & Preprocessor**
   - Create `src/data/loader.py` using Hugging Face's `datasets` library to fetch `ManikaSaini/zomato-restaurant-recommendation`.
   - Create `src/data/preprocessor.py` using `pandas` to:
     - Select and rename columns to match the `Restaurant` schema.
     - Parse comma-separated cuisine strings into lists.
     - Coerce rating/cost data types and handle missing values.
     - Normalize location strings (lowercase/title-case).
     - Compute the `budget_tier` based on `cost_for_two` and predefined thresholds.

4. **Implement Data Repository**
   - Create `src/data/repository.py` acting as an in-memory wrapper for the dataset.
   - Implement caching logic to save/load the preprocessed dataset locally (e.g., as `.csv` or `.parquet`) to avoid repeated downloads.

## Phase 2: Preference Validation & Pre-filtering
**Goal:** Collect user inputs safely and apply deterministic hard constraints to narrow down the dataset before interacting with the LLM.

### Tasks:
1. **Implement User Preference Models**
   - Create `src/models/preferences.py` defining the `UserPreferences` dataclass.

2. **Implement Input Validation**
   - Create `src/services/validator.py` to enforce required fields, budget enums (`low`, `medium`, `high`), rating bounds (0-5), and text normalizations.

3. **Implement Deterministic Filtering Pipeline**
   - Create `src/services/filter.py` with sequential filtering logic:
     - Exact or partial match for `location`.
     - Match for `budget` tier.
     - Filter by `min_rating`.
     - Filter by `cuisine` (if specified).
   - Implement `CandidateSelector` to sort by rating/votes and return the top `N` (e.g., 15-20) candidate restaurants.
   - Implement fallback mechanisms if filtering returns 0 candidates (e.g., relaxing the cuisine or min_rating constraint).

4. **Unit Testing**
   - Write unit tests (`tests/test_filter.py`) using mocked restaurant data to verify filter correctness and edge cases.

## Phase 3: LLM Integration (Groq) & Recommendation Engine
**Goal:** Set up communication with the Groq API, engineer the prompt, and parse the resulting ranked recommendations.

### Tasks:
1. **Setup LLM Client**
   - Create `src/services/llm_client.py` using the `groq` Python SDK.
   - Configure to use `llama-3.3-70b-versatile` via `GROQ_API_KEY`.
   - Implement basic retry logic and exponential backoff for rate limits.

2. **Implement Prompt Builder**
   - Create `src/services/prompt_builder.py` to convert `UserPreferences` and the list of filtered candidate `Restaurant` objects into a structured JSON string.
   - Craft the System Prompt enforcing JSON output and defining the ranking criteria based on soft preferences (e.g., `additional` text).

3. **Implement Recommendation Service Orchestrator**
   - Create `src/services/recommendation.py` bringing together the filter, prompt builder, and LLM client.
   - Create `src/services/parser.py` to safely parse the JSON output from the LLM, validating it against the `RecommendationResponse` schema.
   - Implement logic to merge the LLM's explanation/ranking with the original `Restaurant` objects to fetch missing details for the UI.
   - Implement a heuristic fallback ranking if the LLM completely fails or returns invalid JSON.

## Phase 4: User Interface

Phase 4 is divided into two parts — **Part 1** builds the backend API that serves the UI, and **Part 2** builds the premium frontend application.

---

### Part 1: Backend API (FastAPI)
**Goal:** Expose the recommendation engine through a clean REST API that the frontend will consume.

#### Tasks:
1. **Define API Schemas**
   - Create `src/api/schemas.py` — Pydantic request/response models for all endpoints.

2. **Implement API Routes**
   - Create `src/api/routes.py`:
     - `POST /api/v1/recommend` — Accepts `UserPreferences`, returns top-5 recommendations with AI explanations.
     - `GET /api/v1/locations` — Returns the list of distinct locations for populating dropdowns.
     - `GET /api/v1/cuisines` — Returns the list of distinct cuisines.

3. **Configure App Entry Point**
   - Update `src/main.py` — Mount FastAPI app, configure CORS (to allow the frontend dev server), and run with `uvicorn`.

4. **API Testing**
   - Write `tests/test_api.py` — Use `httpx.AsyncClient` to test all API routes with mocked services.
   - Test end-to-end flow from HTTP request → filtering → LLM → response.

---

### Part 2: Frontend (Next.js)
**Goal:** Deliver a premium, visually stunning web UI that communicates with the FastAPI backend. The frontend should feel like a polished consumer product — not a prototype.

#### Technology & Design System

**Stack:**
- **Framework:** Next.js (App Router) — for SSR, file-based routing, and a production-ready dev experience.
- **Styling:** Vanilla CSS with CSS custom properties (design tokens) — for precise control, micro-animations, and glassmorphism effects.
- **HTTP:** `fetch` / `axios` calling the FastAPI backend at the configured base URL.
- **Icons:** Lucide React (lightweight, consistent icon set).
- **Fonts:** Google Fonts — `Inter` for UI chrome, `Playfair Display` for headings/branding.

**Design Tokens (`globals.css`):**
```css
:root {
  --color-bg-dark:      #0d0f14;
  --color-surface:      #161b26;
  --color-surface-alt:  #1e2535;
  --color-border:       rgba(255,255,255,0.07);
  --color-accent:       #f97316;   /* Zomato-inspired warm orange */
  --color-accent-soft:  rgba(249,115,22,0.15);
  --color-text-primary: #f1f5f9;
  --color-text-muted:   #94a3b8;
  --radius-lg:          16px;
  --shadow-card:        0 4px 32px rgba(0,0,0,0.45);
  --transition-std:     0.22s cubic-bezier(0.4, 0, 0.2, 1);
}
```

#### Tasks:

1. **Application Shell & Navigation**
   - Root Layout (`app/layout.tsx`) — Import Google Fonts; apply dark background; wrap in a context provider for app state.
   - Fixed top nav with app logo/wordmark, glassmorphism backdrop (`backdrop-filter: blur`), and animated underline links.
   - Responsive: collapses to a hamburger menu on mobile.
   - Page routes: `/` (Landing), `/discover` (Search form), `/results` (Results view).

2. **Landing / Hero Page**
   - Full-viewport, deep dark background with a subtle animated mesh/gradient background (CSS keyframe animation).
   - Headline in `Playfair Display`, large (72–96px), e.g., *"Find Your Perfect Table."*
   - Sub-headline in muted text describing the AI-powered nature of the app.
   - CTA Button — Prominent, accent-orange pill button ("Discover Restaurants") with hover glow + scale micro-animation.
   - Feature highlights — Three icon + text cards (Smart Filtering / AI Recommendations / Instant Results) with hover lift effect.
   - Horizontal auto-scrolling ticker of cuisine category chips (Indian, Chinese, Italian, etc.) for visual richness.

3. **Preference / Search Form (`/discover`)**
   - Centered glassmorphism card (`background: rgba(22,27,38,0.8)`, `backdrop-filter: blur(20px)`, `border: 1px solid var(--color-border)`).
   - **Location** — Searchable dropdown populated dynamically via `GET /api/v1/locations`; highlights matching text.
   - **Budget** — Three pill-toggle buttons (Low / Medium / High) with active state animated fill.
   - **Minimum Rating** — Custom star-rating slider: interactive stars that fill on hover/click, with numeric display.
   - **Cuisines** — Multi-select chip grid populated via `GET /api/v1/cuisines`; chips toggle on/off with animated background.
   - **Additional Preferences** — Auto-expanding textarea with character counter; placeholder examples (e.g., *"Rooftop seating, quiet ambience, outdoor dining"*).
   - Inline validation with shake animation on invalid fields.
   - Submit button disabled until required fields are filled; enabled state has a subtle pulse animation.
   - Loading state: frosted-glass overlay with animated progress steps ("Filtering restaurants…", "Consulting AI…", "Ranking results…").

4. **Results View**
   - **Results Header** — Applied filters as dismissible pill badges, "Back to search" link, candidates summary ("AI picked 5 from 312 restaurants in Bellandur").
   - **Recommendation Cards** with staggered entrance animation (slide up + fade in with `animation-delay`):
     - Rank badge (`#1`, `#2`, etc.) in accent-orange with a glow.
     - Restaurant name in large, bold typography.
     - Cuisine tags as pill chips.
     - Star icons + numeric rating + vote count.
     - Estimated cost with `₹` symbol and budget tier badge.
     - **AI Explanation** — Italicized, highlighted blockquote-style text box with a subtle left-border accent. This is the core differentiator.
     - "View on Zomato" link (to `restaurant.url`) with hover underline animation.
   - Card hover state: lifts (`transform: translateY(-4px)`), shadow deepens.
   - Relaxed filters notice — Dismissible amber info banner if constraints were loosened.
   - Empty/error state — Friendly illustrated empty state; toast notifications for API errors.

5. **Polish, Responsiveness & Accessibility**
   - Mobile-first CSS grid/flexbox layouts.
   - Results grid: 1 column (mobile) → 2 columns (tablet) → single-wide cards (desktop).
   - Navigation collapses to drawer on mobile.
   - Page transitions with subtle fade + slide CSS animations.
   - Skeleton loaders on cards while fetching.
   - Semantic HTML5 elements (`<main>`, `<nav>`, `<article>`, `<section>`).
   - ARIA labels on all interactive controls.
   - Focus-visible rings styled to match the design system.
   - Sufficient color contrast ratios (WCAG AA).
   - `NEXT_PUBLIC_API_BASE_URL` env variable pointing to the FastAPI backend.

## Phase 5: Hardening, API Design (Optional), and Delivery
**Goal:** Finalize the application with robust error handling, optional API exposure, and comprehensive documentation.

### Tasks:
1. **Error Handling & Edge Cases**
   - Ensure the UI handles and displays friendly error messages (e.g., "Invalid location", "API Timeout").
   - Add logging throughout the `src/` modules (avoiding logging sensitive keys).

2. **Final Testing & Verification**
   - Test end-to-end flow with diverse inputs (e.g., highly specific queries, vague queries).
   - Verify that the explanation correctly matches the user's "additional" constraints.
   - Verify Lighthouse score ≥ 85 on Performance and Accessibility.
   - Test on Chrome, Firefox, and mobile viewport.

3. **Documentation**
   - Update the root `README.md` with:
     - Overview of the system.
     - Environment setup instructions.
     - Commands to run both the FastAPI backend and the Next.js frontend locally.
     - Screenshots of the key UI screens.
