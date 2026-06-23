export type Citation = {
  source_id: string;
  source_name: string;
  title?: string | null;
  url: string;
  trust_level?: string | null;
  quote?: string | null;
  snippet?: string | null;
  fetched_at?: string | null;
  retrieved_at?: string | null;
};

export type AnswerSource = {
  source_id: string;
  source_name: string;
  url: string;
  category: string;
  geography: string;
  language: string;
  trust_level: string;
};

export type IngestionStatus = {
  ready_for_keyword_retrieval: boolean;
  ready_for_vector_retrieval: boolean;
  raw_documents_count: number;
  chunk_files_count: number;
  chunks_count: number;
  vector_files_count: number;
  vectors_count: number;
  warnings: string[];
  raw_dir: string;
  chunks_dir: string;
  vectors_dir: string;
};

export type AskResponse = {
  answer: string;
  language: string;
  confidence: string;
  citations: Citation[];
  sources: AnswerSource[];
  safety_note?: string | null;
  ingestion_status?: IngestionStatus | null;
};

export type AskRequest = {
  question: string;
  language?: string;
};

export class SanJuanApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SanJuanApiError";
  }
}

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return (process.env.NEXT_PUBLIC_SANJUAN_API_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

export async function askSanJuanAI(payload: AskRequest): Promise<AskResponse> {
  const question = payload.question.trim();

  if (!question) {
    throw new SanJuanApiError("Please enter a question before asking SanJuan AI.");
  }

  const response = await fetch(`${getApiBaseUrl()}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      language: payload.language || undefined,
    }),
  }).catch(() => {
    throw new SanJuanApiError(
      "SanJuan AI could not reach the backend. Make sure the FastAPI server is running on http://127.0.0.1:8000."
    );
  });

  if (!response.ok) {
    let detail = `The backend returned ${response.status}.`;

    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // Keep the default detail when the backend does not return JSON.
    }

    throw new SanJuanApiError(detail);
  }

  return response.json() as Promise<AskResponse>;
}
