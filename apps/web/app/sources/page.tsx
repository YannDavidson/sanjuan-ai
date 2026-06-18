import { formatLabel, getSources, uniqueValues } from "@/lib/sources";

type SearchParams = Promise<{
  category?: string;
  trust_level?: string;
  geography?: string;
  language?: string;
}>;

function FilterSelect({ name, label, value, options }: { name: string; label: string; value?: string; options: string[] }) {
  return (
    <label>
      <span className="badge">{label}</span>
      <select name={name} defaultValue={value ?? ""}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {formatLabel(option)}
          </option>
        ))}
      </select>
    </label>
  );
}

export default async function SourcesPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  const sources = getSources();
  const filteredSources = sources.filter((source) => {
    if (params.category && source.category !== params.category) return false;
    if (params.trust_level && source.trust_level !== params.trust_level) return false;
    if (params.geography && source.geography !== params.geography) return false;
    if (params.language && source.language !== params.language) return false;
    return true;
  });

  return (
    <section className="container section">
      <div className="eyebrow">Source Registry</div>
      <h1>Trusted Puerto Rico sources.</h1>
      <p className="lede">
        The SanJuan AI source registry is the foundation of the assistant. These sources will be used for retrieval,
        citation cards, trust scoring, and high-risk answer safety.
      </p>

      <form className="filters">
        <FilterSelect name="category" label="Category" value={params.category} options={uniqueValues(sources, "category")} />
        <FilterSelect
          name="trust_level"
          label="Trust level"
          value={params.trust_level}
          options={uniqueValues(sources, "trust_level")}
        />
        <FilterSelect name="geography" label="Geography" value={params.geography} options={uniqueValues(sources, "geography")} />
        <FilterSelect name="language" label="Language" value={params.language} options={uniqueValues(sources, "language")} />
        <button className="button primary" type="submit">
          Apply filters
        </button>
        <a className="button" href="/sources">
          Reset
        </a>
      </form>

      <p>
        Showing <strong>{filteredSources.length}</strong> of <strong>{sources.length}</strong> sources.
      </p>

      <div className="source-grid">
        {filteredSources.map((source) => (
          <article className="card" key={source.id}>
            <div className="badge-row">
              <span className={`badge ${source.trust_level === "official" ? "official" : ""}`}>{source.trust_level}</span>
              <span className="badge">{formatLabel(source.category)}</span>
              <span className="badge">{formatLabel(source.language)}</span>
            </div>
            <h3>{source.name}</h3>
            <p>{source.notes}</p>
            <div className="badge-row">
              <span className="badge">{formatLabel(source.geography)}</span>
              <span className="badge">{formatLabel(source.source_type)}</span>
              {source.update_frequency ? <span className="badge">{formatLabel(source.update_frequency)}</span> : null}
            </div>
            <a className="button" href={source.url} target="_blank" rel="noreferrer">
              Open source
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}
