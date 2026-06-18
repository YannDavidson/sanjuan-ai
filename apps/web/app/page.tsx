import Link from "next/link";

const useCases = [
  "Find Puerto Rico government services without hunting across dozens of sites.",
  "Help founders discover business registration, incentives, permits, and support programs.",
  "Give visitors and residents a trusted bilingual assistant for San Juan and beyond.",
];

const principles = [
  "Official sources first for high-risk information.",
  "Citations and source cards in the answer experience.",
  "English and Spanish by default, built for Puerto Rican context.",
];

export default function HomePage() {
  return (
    <div>
      <section className="container hero">
        <div className="eyebrow">Puerto Rico first · Bilingual · Citation-first</div>
        <h1>Modern Caribbean Intelligence for Puerto Rico.</h1>
        <p className="lede">
          SanJuan AI is an AI-native public knowledge infrastructure layer for Puerto Rico, starting with trusted sources,
          civic information, tourism, business resources, weather, and local discovery.
        </p>
        <div className="actions">
          <Link className="button primary" href="/ask">
            Ask SanJuan AI
          </Link>
          <Link className="button" href="/sources">
            Explore trusted sources
          </Link>
        </div>
      </section>

      <section className="container section">
        <h2>Built as a source-grounded assistant, not a generic chatbot.</h2>
        <div className="grid">
          {useCases.map((item) => (
            <article className="card" key={item}>
              <h3>Use case</h3>
              <p>{item}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="card strong">
          <div className="eyebrow">Trust model</div>
          <h2>Citations are part of the product experience.</h2>
          <p>
            The assistant will prioritize official Puerto Rico sources for taxes, permits, health, legal, public benefits,
            emergency, police, court, immigration, and safety-related questions. When evidence is weak, SanJuan AI should
            say so and guide users back to trusted sources.
          </p>
          <div className="grid">
            {principles.map((item) => (
              <div className="card" key={item}>
                <p>{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="container footer-note">
        MVP status: source registry and FastAPI backend are live in the repo. Retrieval and web UI are being built around a
        citation-first architecture.
      </footer>
    </div>
  );
}
