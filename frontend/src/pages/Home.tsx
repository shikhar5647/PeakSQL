import { Link } from "react-router-dom";
import { LogoMark } from "../components/Logo";
import Reveal from "../components/Reveal";

const STACK = ["LangGraph", "Neo4j", "Gemini", "vLLM", "Arctic-Text2SQL", "FastAPI", "React"];

const PHASES = [
  { n: "01", icon: "📥", name: "Ingest", desc: "schema + real data profiled" },
  { n: "02", icon: "🧠", name: "Enrich", desc: "descriptions, synonyms, PII tags" },
  { n: "03", icon: "🕸️", name: "Connect", desc: "declared + discovered joins" },
  { n: "04", icon: "📈", name: "Understand", desc: "metrics, KPIs, query patterns" },
  { n: "05", icon: "🗄️", name: "Materialize", desc: "knowledge graph in Neo4j" },
  { n: "06", icon: "✅", name: "Validate", desc: "gate: nothing broken ships" },
];

export default function Home() {
  return (
    <div className="page landing">
      {/* ── Hero ─────────────────────────────────────────── */}
      <section className="hero hero2">
        <div className="hero-grid">
          <div className="hero-copy">
            <span className="hero-badge">
              <LogoMark size={15} /> Knowledge-graph powered Text-to-SQL
            </span>
            <h1>
              Ask your database anything.
              <br />
              <span className="grad">In plain English.</span>
            </h1>
            <p className="hero-sub">
              PeakSQL builds a <b>knowledge-graph semantic layer</b> over your database — every
              table, column, relationship, metric and business term, understood and connected — so
              the SQL it writes is grounded in <i>your</i> data, not a language model's guess.
            </p>
            <div className="cta-row left">
              <Link to="/studio" className="btn-cta primary">
                Open the Studio →
              </Link>
              <a href="#how" className="btn-cta">
                How it works
              </a>
            </div>
            <div className="ministats">
              <span><b>13</b> specialist agents</span>
              <span className="msep" />
              <span><b>9</b> parallel waves</span>
              <span className="msep" />
              <span><b>100%</b> of the pipeline visible</span>
            </div>
          </div>

          {/* the product, in one card */}
          <div className="demo-card-wrap">
            <div className="demo-card">
              <div className="demo-title">
                <span className="tl-dot r" /><span className="tl-dot y" /><span className="tl-dot g" />
                <span className="demo-name">PeakSQL · query</span>
              </div>
              <div className="demo-q">
                “What was our <mark>revenue</mark> by <mark>product category</mark> last month?”
                <span className="caret" />
              </div>
              <div className="demo-resolve">
                <div className="demo-label">resolved through the knowledge graph</div>
                <div className="res-row"><span className="res-chip metric">Metric</span> revenue → <code>SUM(orders.ord_amt)</code></div>
                <div className="res-row"><span className="res-chip col">Column</span> category → <code>products.prod_cat</code></div>
                <div className="res-row"><span className="res-chip rel">Join</span> <code>order_items ⋈ products</code> <span className="res-note">discovered · conf 0.98</span></div>
              </div>
              <pre className="demo-sql">{`SELECT p.prod_cat, SUM(o.ord_amt) AS revenue
FROM orders o
JOIN order_items oi ON oi.ord_id = o.ord_id
JOIN products p    ON p.prod_id = oi.prod_id
WHERE o.ord_dt >= date('now','start of month','-1 month')
GROUP BY p.prod_cat ORDER BY revenue DESC;`}</pre>
              <div className="demo-result">✓ 5 rows · 240 ms · confidence 0.94</div>
            </div>
            <div className="demo-glow" />
          </div>
        </div>

        <div className="stack-strip">
          <span className="stack-label">built with</span>
          {STACK.map((s) => (
            <span className="stack-chip" key={s}>{s}</span>
          ))}
        </div>
      </section>

      {/* ── Why it matters ───────────────────────────────── */}
      <Reveal>
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
              <div className="ic-chip">📊</div>
              <h3>Business teams</h3>
              <p>"What was revenue by region last quarter?" answered in seconds — self-serve analytics without waiting on a dashboard request.</p>
            </div>
            <div className="feature-card">
              <div className="ic-chip">🏦</div>
              <h3>Finance & banking</h3>
              <p>Metrics with governed definitions — "revenue" means the same formula every time, with compliance tags tracked in the graph.</p>
            </div>
            <div className="feature-card">
              <div className="ic-chip">🏥</div>
              <h3>Healthcare</h3>
              <p>Query patient and operations data safely — PHI columns are identified and tagged during graph construction, before a single query runs.</p>
            </div>
            <div className="feature-card">
              <div className="ic-chip">🛒</div>
              <h3>Retail & operations</h3>
              <p>Inventory, orders, fulfillment — everyday operational questions answered directly from the source of truth, in everyday language.</p>
            </div>
          </div>
        </section>
      </Reveal>

      {/* ── Comparison: the pitch ────────────────────────── */}
      <Reveal>
        <section className="section alt">
          <h2 className="landing-h2">Why plain LLM-to-SQL isn't enough</h2>
          <p className="section-sub">
            Point a language model at a schema and it guesses — confidently. PeakSQL makes it
            consult a semantic layer instead. That's the whole difference between a demo and a
            product you can trust:
          </p>
          <div className="vs-grid">
            <div className="vs-card bad">
              <div className="vs-head">Plain LLM text-to-SQL</div>
              <ul>
                <li><span className="x">✕</span><span>Guesses joins from column names — and hallucinates the ones it can't find</span></li>
                <li><span className="x">✕</span><span>Has no idea your team says “clients” for the <code>customers</code> table</span></li>
                <li><span className="x">✕</span><span>“Revenue” means whatever the model feels like today</span></li>
                <li><span className="x">✕</span><span>A black box — when it's wrong, you can't see why</span></li>
              </ul>
            </div>
            <div className="vs-card good">
              <div className="vs-head"><LogoMark size={16} /> PeakSQL</div>
              <ul>
                <li><span className="c">✓</span><span>Joins come from verified relationships — declared FKs <i>and</i> discovered ones, each with a confidence score</span></li>
                <li><span className="c">✓</span><span>A synonym & phrase layer maps how people talk to how data is stored</span></li>
                <li><span className="c">✓</span><span>Metrics are discovered once, defined precisely, reused everywhere</span></li>
                <li><span className="c">✓</span><span>Every agent decision is streamed, inspectable and validation-gated</span></li>
              </ul>
            </div>
          </div>
        </section>
      </Reveal>

      {/* ── Pipeline strip ───────────────────────────────── */}
      <Reveal>
        <section className="section">
          <h2 className="landing-h2">From raw schema to semantic brain — automatically</h2>
          <p className="section-sub">
            Thirteen specialist agents, orchestrated with LangGraph across 9 parallel,
            checkpointed waves. Watch every one of them think, live, in the Studio.
          </p>
          <div className="phase-strip">
            {PHASES.map((p, i) => (
              <div className="phase-step" key={p.n}>
                <div className="phase-pill">
                  <span className="phase-ic">{p.icon}</span>
                  <div>
                    <div className="phase-name">{p.n} · {p.name}</div>
                    <div className="phase-desc">{p.desc}</div>
                  </div>
                </div>
                {i < PHASES.length - 1 && <span className="phase-arrow">→</span>}
              </div>
            ))}
          </div>
        </section>
      </Reveal>

      {/* ── How it works ─────────────────────────────────── */}
      <Reveal>
        <section className="section" id="how">
          <h2 className="landing-h2">How PeakSQL works</h2>
          <div className="stage-grid">
            <div className="stage-card">
              <div className="stage-tag live">Stage 1 · live now</div>
              <h3>Build the semantic layer</h3>
              <p>
                Upload a <code>.db</code>, <code>.csv</code> or schema <code>.json</code>. The agent
                pipeline profiles your data, describes every entity, discovers relationships the
                schema never declared, mines metrics and synonyms, and materializes it all as a
                knowledge graph (in-memory + Neo4j). A validation gate blocks anything incomplete.
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
                At question time, PeakSQL resolves your words through the graph — synonyms →
                entities → join paths → metric formulas — and hands that curated context to{" "}
                <b>Arctic-Text2SQL-R1</b>, a 7B reasoning model purpose-trained for SQL generation.
                The query is validated, scored for confidence, executed, and the answer comes back
                in plain language.
              </p>
              <p>Evaluation target: execution accuracy on BIRD — the industry-standard benchmark.</p>
            </div>
          </div>
        </section>
      </Reveal>

      {/* ── Final CTA ────────────────────────────────────── */}
      <Reveal>
        <section className="cta-band">
          <LogoMark size={40} />
          <h2>See the semantic layer build itself.</h2>
          <p>One click. Thirteen agents. Every thought on screen.</p>
          <Link to="/studio" className="btn-cta primary">
            Launch the Studio →
          </Link>
        </section>
      </Reveal>

      {/* ── Footer ───────────────────────────────────────── */}
      <footer className="landing-footer big">
        <div className="foot-brand">
          <LogoMark size={20} />
          <span className="logo">Peak<em>SQL</em></span>
          <span className="foot-tag">The semantic layer is the product.</span>
        </div>
        <div className="foot-links">
          <Link to="/studio">Studio</Link>
          <Link to="/team">Team</Link>
          <a href="https://github.com/shikhar5647/PeakSQL" target="_blank" rel="noreferrer">GitHub</a>
          <a href="https://www.linkedin.com/in/shikhar-dave-400810258/" target="_blank" rel="noreferrer">LinkedIn</a>
        </div>
        <div className="foot-copy">Built by Shikhar Dave · IIT Jodhpur</div>
      </footer>
    </div>
  );
}
