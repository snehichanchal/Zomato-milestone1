"use client";

import { useState, useEffect } from "react";
import styles from "./page.module.css";
import LocationDropdown from "@/components/LocationDropdown";
import RecommendationCard from "@/components/RecommendationCard";
import LoadingState from "@/components/LoadingState";
import EmptyState from "@/components/EmptyState";
import ErrorBanner from "@/components/ErrorBanner";
import {
  getLocations,
  getCuisines,
  getRecommendations,
  type RecommendationResponse,
} from "@/lib/api";

type AppState = "idle" | "loading" | "success" | "error" | "empty";

export default function DiscoverPage() {
  // --- Form state ---
  const [location, setLocation] = useState("");
  const [budget, setBudget] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [minRating, setMinRating] = useState(4.0);
  const [additional, setAdditional] = useState("");

  // --- Data from API ---
  const [locations, setLocations] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);

  // --- Results state ---
  const [appState, setAppState] = useState<AppState>("idle");
  const [results, setResults] = useState<RecommendationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    async function fetchDropdowns() {
      try {
        const [locs, cuiss] = await Promise.all([
          getLocations(),
          getCuisines(),
        ]);
        if (isMounted) {
          setLocations(locs);
          setCuisines(cuiss);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Failed to load dropdown data, retrying in 2s...", err);
          timeoutId = setTimeout(fetchDropdowns, 2000);
        }
      }
    }
    fetchDropdowns();

    return () => {
      isMounted = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, []);

  // --- Form validation ---
  const isFormValid = location.trim() !== "" && budget !== "";

  // --- Submit handler ---
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isFormValid) return;

    setAppState("loading");
    setErrorMessage("");
    setResults(null);

    try {
      const response = await getRecommendations({
        location,
        budget,
        cuisine: cuisine || undefined,
        min_rating: minRating,
        additional: additional || undefined,
      });

      if (response.recommendations.length === 0) {
        setAppState("empty");
        setResults(response);
      } else {
        setAppState("success");
        setResults(response);
      }
    } catch (err: unknown) {
      setAppState("error");
      const message =
        err instanceof Error ? err.message : "An unexpected error occurred.";
      setErrorMessage(message);
    }
  }

  return (
    <div className={`container ${styles.page}`}>
      {/* Error Banner */}
      {appState === "error" && errorMessage && (
        <ErrorBanner
          message={errorMessage}
          onDismiss={() => setErrorMessage("")}
        />
      )}

      <div className={styles.layout}>
        {/* Left Column: Preferences Form */}
        <aside className={styles.sidebar}>
          <div className={styles.formCard}>
            <h2 className={styles.formTitle}>
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 24, color: "var(--color-primary)" }}
              >
                tune
              </span>
              Your preferences
            </h2>

            <form className={styles.form} onSubmit={handleSubmit}>
              {/* Location */}
              <div className={styles.field}>
                <label className="form-label">Location</label>
                <LocationDropdown
                  locations={locations}
                  value={location}
                  onChange={setLocation}
                  placeholder="Search for a city or area…"
                />
              </div>

              {/* Budget */}
              <div className={styles.field}>
                <label className="form-label">Budget (for two)</label>
                <select
                  className="form-input"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                >
                  <option value="">Select budget</option>
                  <option value="low">Low &lt;₹500</option>
                  <option value="medium">Medium ₹501-1500</option>
                  <option value="high">High &gt;₹1500</option>
                </select>
              </div>

              {/* Cuisine */}
              <div className={styles.field}>
                <label className="form-label">Cuisine Preference</label>
                <select
                  className="form-input"
                  value={cuisine}
                  onChange={(e) => setCuisine(e.target.value)}
                >
                  <option value="">Any cuisine</option>
                  {cuisines.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Min Rating Slider */}
              <div className={styles.field}>
                <div className={styles.ratingHeader}>
                  <label className="form-label">Minimum Rating</label>
                  <span className={styles.ratingValue}>{minRating.toFixed(1)}+</span>
                </div>
                <input
                  type="range"
                  className={styles.slider}
                  min="0"
                  max="5"
                  step="0.5"
                  value={minRating}
                  onChange={(e) => setMinRating(parseFloat(e.target.value))}
                />
                <div className={styles.sliderLabels}>
                  <span>Any</span>
                  <span>5.0</span>
                </div>
              </div>

              {/* Additional Context */}
              <div className={styles.field}>
                <label className="form-label">Additional Context (Optional)</label>
                <textarea
                  className={`form-input ${styles.textarea}`}
                  value={additional}
                  onChange={(e) => setAdditional(e.target.value)}
                  placeholder="e.g., 'Looking for a quiet place for a date night', 'Needs to have good vegetarian options', 'Outdoor seating preferred'"
                  maxLength={500}
                />
                <div className={styles.charCount}>
                  {additional.length} / 500
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                className="btn-primary"
                disabled={!isFormValid || appState === "loading"}
              >
                <span className="material-symbols-outlined" style={{ fontSize: 20 }}>
                  auto_awesome
                </span>
                {appState === "loading" ? "Finding..." : "Get AI Recommendations"}
              </button>
            </form>
          </div>
        </aside>

        {/* Right Column: Results */}
        <section className={styles.results}>
          {/* Filter chips (decorative for now) */}
          {appState === "success" && results && (
            <div className={styles.filterRow}>
              <div className={styles.filterChips}>
                {results.metadata.filters_applied &&
                  Object.entries(results.metadata.filters_applied).map(
                    ([key, val]) => (
                      <span key={key} className="chip">
                        {key === "location" && "📍 "}
                        {key === "budget" && "💰 "}
                        {key === "min_rating" && "⭐ "}
                        {key === "cuisine" && "🍽️ "}
                        {String(val)}
                      </span>
                    )
                  )}
              </div>
              <span className={styles.sortLabel}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>
                  sort
                </span>
                Sort by: Relevance
              </span>
            </div>
          )}

          {/* Relaxed constraints notice */}
          {results?.metadata.constraints_relaxed &&
            results.metadata.constraints_relaxed.length > 0 && (
              <div className={styles.relaxedBanner}>
                <span className="material-symbols-outlined" style={{ fontSize: 18, color: "#f59e0b" }}>
                  info
                </span>
                <span>
                  Some filters were relaxed to find results.{" "}
                  {results.metadata.constraints_relaxed.join(", ")} filter
                  {results.metadata.constraints_relaxed.length > 1 ? "s were" : " was"}{" "}
                  removed.
                </span>
              </div>
            )}

          {/* AI Summary Banner */}
          {appState === "success" && results?.summary && (
            <div className={styles.aiBanner}>
              <div className={styles.aiBannerGlow1} />
              <div className={styles.aiBannerGlow2} />
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 24, color: "var(--color-primary)", flexShrink: 0, zIndex: 1 }}
              >
                auto_awesome
              </span>
              <div className={styles.aiBannerText}>
                <span className={styles.aiBannerTitle}>AI Recommendation Summary</span>
                <p className={styles.aiBannerDesc}>{results.summary}</p>
              </div>
            </div>
          )}

          {/* Loading */}
          {appState === "loading" && <LoadingState />}

          {/* Empty */}
          {appState === "empty" && <EmptyState />}

          {/* Idle */}
          {appState === "idle" && (
            <div className={styles.idleState}>
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 48, color: "var(--color-surface-container-highest)" }}
              >
                restaurant_menu
              </span>
              <p className={styles.idleText}>
                Fill in your preferences and hit <strong>&quot;Get AI Recommendations&quot;</strong> to see personalized results here.
              </p>
            </div>
          )}

          {/* Results Cards */}
          {appState === "success" && results && (
            <div className={styles.cardList}>
              {results.recommendations.map((item, idx) => (
                <RecommendationCard key={item.restaurant_id} item={item} index={idx} />
              ))}
            </div>
          )}

          {/* Metadata footer */}
          {appState === "success" && results && (
            <div className={styles.metaFooter}>
              Powered by {results.metadata.model || "AI"} •{" "}
              {results.metadata.total_restaurants} restaurants scanned •{" "}
              {results.metadata.candidates_considered} candidates considered
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
