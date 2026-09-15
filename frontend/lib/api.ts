import type {
  AssessmentRequest,
  AssessmentResponse,
  ExplanationResponse,
} from "@/types/assessment";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = (await response.json().catch(() => null)) as
    | { error?: { code?: string; message?: string } }
    | null;
  if (!response.ok) {
    throw new ApiError(
      response.status,
      body?.error?.code ?? "request_failed",
      body?.error?.message ?? "The request could not be completed.",
    );
  }
  return body as T;
}

export function predictAssessment(
  payload: AssessmentRequest,
): Promise<AssessmentResponse> {
  return request<AssessmentResponse>("/api/assessment/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function requestExplanation(
  payload: AssessmentRequest,
): Promise<ExplanationResponse> {
  return request<ExplanationResponse>("/api/assessment/explanation", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export { ApiError };
