"use client";

import { FormEvent, useState } from "react";

import { AskResponse, askSanJuanAI } from "../../lib/api";

const exampleQuestions = [
  "How do I register a business in Puerto Rico?",
  "Where can I find San Juan municipal services?",
  "What official sources should I check for hurricane alerts?",
];

const defaultQuestion = "Where do I start if I want to register a business in Puerto Rico?";

export default function AskPage() {
  const [question, setQuestion] = useState(defaultQuestion);
  const [language, setLanguage] = useState("en");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await askSanJuanAI({ question, language });
      setAnswer(response);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Something went wrong.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  const ingestion = answer?.ingestion_status;
  const hasCorpusWarnings = Boolean(ingestion?.warnings?.length);

  return (
    <section className="container section">
      <div className="eyebrow">Ask SanJuan AI</div>
      <h1>Ask with sources, not guesses.</h1>
      <p className="lede">
        This page calls the FastAPI backend and renders SanJuan AI's citation-first answer contract: direct answer,
        confidence, citations, source cards, safety notes, and corpus readiness.
      </p>

      <div className="chat-shell section">
        <form className="card strong" onSubmit={handleSubmit}>
          <label htmlFor="question">
            <h3>Your question</h3>
          </label>
          <textarea
            id="question"
            placeholder="Ask about Puerto Rico services, San Juan resources, permits, tourism, weather, or business support..."
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />

          <label htmlFor="language">
            <h3>Preferred language</h3>
          </label>
          <select id="language" value={language} onChange={(event) => setLanguage(event.target.value)}>
            <option value="en">English</option>
            <option value="es">Español</option>
          </select>

          <div className="actions">
            <button className="button primary" type="submit" disabled={isLoading}>
              {isLoading ? "Asking..." : "Ask SanJuan AI"}
            </button>
            <span className="badge">Hybrid retrieval</span>
          </div>

          {error && <p className="error-message">{error}</p>}
        </form>

        <aside className="card">
          <h3>Example questions</h3>
          {exampleQuestions.map((item) => (
            <button className="example-question" key={item} type="button" onClick={() => setQuestion(item)}>
              → {item}
            </button>
          ))}
        </aside>
      </div>

      {answer ? (
        <div className="card strong">
          <div className="eyebrow">Backend response</div>
          <div className="answer-box">
            <h2>{answer.answer}</h2>
            <div className="badge-row">
              <span className="badge">confidence: {answer.confidence}</span>
              <span className="badge">language: {answer.language}</span>
              <span className="badge official">citation-first contract</span>
            </div>
            {answer.safety_note && <p className="safety-note">{answer.safety_note}</p>}
          </div>

          {ingestion && (
            <section className="section compact-section">
              <h2>Corpus readiness</h2>
              {hasCorpusWarnings && (
                <div className="notice">
                  <strong>Answer may be limited.</strong>
                  <ul>
                    {ingestion.warnings.map((warning) => (
                      <li key={warning}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="metric-grid compact-metrics">
                <div className="metric-card">
                  <span>Raw docs</span>
                  <strong>{ingestion.raw_documents_count}</strong>
                </div>
                <div className="metric-card">
                  <span>Chunks</span>
                  <strong>{ingestion.chunks_count}</strong>
                </div>
                <div className="metric-card">
                  <span>Vectors</span>
                  <strong>{ingestion.vectors_count}</strong>
                </div>
                <div className="metric-card">
                  <span>Mode</span>
                  <strong>{ingestion.ready_for_vector_retrieval ? "hybrid" : "keyword"}</strong>
                </div>
              </div>
            </section>
          )}

          <section className="section compact-section">
            <h2>Citations</h2>
            {answer.citations.length > 0 ? (
              <div className="source-grid">
                {answer.citations.map((citation) => (
                  <article className="card" key={`${citation.source_id}-${citation.url}`}>
                    <div className="badge-row">
                      <span className="badge official">citation</span>
                      <span className="badge">{citation.source_id}</span>
                    </div>
                    <h3>{citation.source_name}</h3>
                    {citation.quote && <p>“{citation.quote}”</p>}
                    {citation.snippet && <p>{citation.snippet}</p>}
                    {citation.fetched_at && <p className="muted">Fetched: {citation.fetched_at}</p>}
                    <a className="button" href={citation.url} target="_blank" rel="noreferrer">
                      Open citation
                    </a>
                  </article>
                ))}
              </div>
            ) : (
              <p>No citations yet. Retrieval will populate this area once source chunking and search are connected.</p>
            )}
          </section>

          <section className="section compact-section">
            <h2>Relevant trusted sources</h2>
            <div className="source-grid">
              {answer.sources.map((source) => (
                <article className="card" key={source.source_id}>
                  <div className="badge-row">
                    <span className={source.trust_level === "official" ? "badge official" : "badge"}>
                      {source.trust_level}
                    </span>
                    <span className="badge">{source.category}</span>
                    <span className="badge">{source.language}</span>
                  </div>
                  <h3>{source.source_name}</h3>
                  <p>
                    {source.geography} · {source.source_id}
                  </p>
                  <a className="button" href={source.url} target="_blank" rel="noreferrer">
                    Open source
                  </a>
                </article>
              ))}
            </div>
          </section>
        </div>
      ) : (
        <div className="card strong">
          <div className="eyebrow">Ready for retrieval</div>
          <div className="answer-box">
            <h2>Ask a question to test hybrid retrieval.</h2>
            <p>
              The backend now uses local hybrid retrieval. Run ingestion, chunking, and vector build to unlock the strongest
              source-grounded answers.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
