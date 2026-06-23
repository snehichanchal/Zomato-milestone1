/**
 * API client for the FastAPI backend.
 *
 * All calls go through the base URL configured in NEXT_PUBLIC_API_BASE_URL.
 */

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/* ------------------------------------------------------------------ */
/*  Types                                                             */
/* ------------------------------------------------------------------ */

export interface RecommendationItem {
  rank: number;
  name: string;
  cuisine: string;
  rating: number;
  estimated_cost: number;
  explanation: string;
  restaurant_id: string;
}

export interface RecommendationResponse {
  summary: string | null;
  recommendations: RecommendationItem[];
  metadata: {
    candidates_considered: number;
    total_restaurants: number;
    filters_applied: Record<string, string>;
    model?: string;
    constraints_relaxed?: string[];
  };
}

export interface RecommendationRequest {
  location: string;
  budget: string;
  cuisine?: string | null;
  min_rating?: number;
  additional?: string | null;
}

export interface LocationsResponse {
  locations: string[];
}

export interface CuisinesResponse {
  cuisines: string[];
}

/* ------------------------------------------------------------------ */
/*  API Functions                                                     */
/* ------------------------------------------------------------------ */

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message =
      typeof body.detail === "string"
        ? body.detail
        : "An error occurred while contacting the server.";
    throw new ApiError(message, res.status);
  }

  return res.json() as Promise<T>;
}

/** Fetch the list of distinct locations for populating the dropdown. */
export async function getLocations(): Promise<string[]> {
  const data = await request<LocationsResponse>("/api/v1/locations");
  return data.locations;
}

/** Fetch the list of distinct cuisines for populating the dropdown. */
export async function getCuisines(): Promise<string[]> {
  const data = await request<CuisinesResponse>("/api/v1/cuisines");
  return data.cuisines;
}

/** Submit user preferences and get AI-ranked recommendations. */
export async function getRecommendations(
  payload: RecommendationRequest
): Promise<RecommendationResponse> {
  return request<RecommendationResponse>("/api/v1/recommend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
