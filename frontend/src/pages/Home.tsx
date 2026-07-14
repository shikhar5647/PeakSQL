import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="page landing">
      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="hero">
        <span className="hero-badge">Knowledge-graph powered Text-to-SQL</span>
        <h1>
          Ask your database anything.
          <br />
          <span className="grad">In plain English.</span>
        </h1>
        <p className="hero-sub">
          PeakSQL builds a <b>knowledge-graph semantic layer</b> over your database — every table,
          column, relationship, metric and business term, understood and connected — so the SQL it
          writes is grounded in <i>your</i> data, not a language model's guess.
        </p>
        <div className="cta-row">
          <Link to="/studio" className="btn-cta primary">
            Open the Studio →
          </Link>
          <a href="#how" className="btn-cta">
            How it works
          </a>
        </div>
        <div className="stat-strip">
          <div className="stat">
            <div className="v">13</div>
            <div className="l">specialist agents</div>
          </div>
          <div className="stat">
            <div className="v">9</div>
            <div className="l">parallel execution waves</div>
          </div>
          <div className="stat">
            <div className="v">7</div>
            <div className="l">knowledge node types</div>
          </div>
          <div className="stat">
            <div className="v">100%</div>
            <div className="l">of the pipeline visible live</div>
          </div>
        </div>
      </section>

      {/* ── Why it matters ───────────────────────────────── */}
      <section className="section">
        <h2 className="landing-h2">Every company runs on SQL. Almost nobody speaks it.</h2>
        <p className="section-sub">
          The world's operational truth — sales, patients, shipments, transactions — lives in
          relational databases. But the people with the questions are analysts, doctors, managers
          and founders, not SQL experts. So every question waits in a queue behind a data team,
          and most questions simply never get asked.
        </p>
        <div className="cards four">
          <div className="feature-card">
            <div className="ic">📊</div>
            <h3>Business teams</h3>
            <p>"What was revenue by region last quarter?" answered in seconds — self-serve analytics without waiting on a dashboard request.</p>
          </div>
          <div className="feature-card">
            <div className="ic">🏦</div>
            <h3>Finance & banking</h3>
            <p>Metrics with governed definitions — "revenue" means the same formula every time, with compliance tags (PII, financial) tracked in the graph.</p>
          </div>
          <div className="feature-card">
            <div className="ic">🏥</div>
            <h3>Healthcare</h3>
            <p>Query patient and operations data safely — PHI columns are identified and tagged during graph construction, before a single query runs.</p>
          </div>
          <div className="feature-card">
            <div className="ic">🛒</div>
            <h3>Retail & operations</h3>
            <p>Inventory, orders, fulfillment — everyday operational questions answered directly from the source of truth, in everyday language.</p>
          </div>
        </div>
      </section>

      {/* ── The problem with naive text2sql ──────────────── */}
      <section className="section alt">
        <h2 className="landing-h2">Why plain LLM-to-SQL isn't enough</h2>
        <p className="section-sub">
          Point a language model at a schema and it will guess — and confidently. It hallucinates
          joins, mistakes <code>cust_addr_zip</code> for a price column, and has no idea that your
          team says "clients" for the <code>customers</code> table. PeakSQL fixes this with a
          semantic layer the model must consult:
        </p>
        <div className="cards three">
          <div className="feature-card">
            <div className="ic">🧠</div>
            <h3>Understands your names</h3>
            <p>
              <code>cust_addr_zip</code> → Customer · Address · Zip Code. Every cryptic column gets
              technical, business and short descriptions, generated with real data samples as context.
            </p>
          </div>
          <div className="feature-card">
            <div className="ic">🕸️</div>
            <h3>Discovers hidden relationships</h3>
            <p>
              30–60% of real-world joins are never declared as foreign keys. PeakSQL finds them via
              value-overlap, naming and semantic analysis — each with a confidence score.
            </p>
          </div>
          <div className="feature-card">
            <div className="ic">🗣️</div>
            <h3>Speaks your language</h3>
            <p>
              "revenue" = "sales" = <code>SUM(orders.ord_amt)</code>. Synonyms, phrase mappings and
              discovered metrics bridge how people talk to how data is stored.
            </p>
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────── */}
      <section className="section" id="how">
        <h2 className="landing-h2">How PeakSQL works</h2>
        <div className="stage-grid">
          <div className="stage-card">
            <div className="stage-tag live">Stage 1 · live now</div>
            <h3>Build the semantic layer</h3>
            <p>
              Upload a <code>.db</code>, <code>.csv</code> or schema <code>.json</code>. Thirteen
              specialist agents — orchestrated with LangGraph, running in 9 parallel waves with
              checkpointing — profile your data, describe every entity, discover relationships,
              mine metrics and synonyms, and materialize it all as a knowledge graph (in-memory +
              Neo4j). A validation gate blocks anything incomplete.
            </p>
            <p>
              Every agent's status, thought process and LLM calls stream live in the Studio —
              nothing is a black box.
            </p>
            <Link to="/studio" className="btn-cta primary sm">
              Watch it run →
            </Link>
          </div>
          <div className="stage-card">
            <div className="stage-tag soon">Stage 2 · in design</div>
            <h3>Ask questions, get grounded SQL</h3>
            <p>
              At question time, PeakSQL resolves your words through the graph — synonyms → entities
              → join paths → metric formulas — and hands that curated context to{" "}
              <b>Arctic-Text2SQL-R1</b>, a 7B reasoning model purpose-trained for SQL generation.
              The query is validated, scored for confidence, executed, and the answer comes back in
              plain language.
            </p>
            <p>Evaluation target: execution accuracy on BIRD — the industry-standard benchmark.</p>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────── */}
      <footer className="landing-footer">
        <span>
          Built by <Link to="/team">Shikhar Dave</Link> · IIT Jodhpur
        </span>
        <span className="dotsep">·</span>
        <a href="https://github.com/shikhar5647/PeakSQL" target="_blank" rel="noreferrer">
          GitHub
        </a>
        <span className="dotsep">·</span>
        <a href="https://www.linkedin.com/in/shikhar-dave-400810258/" target="_blank" rel="noreferrer">
          LinkedIn
        </a>
      </footer>
    </div>
  );
}
