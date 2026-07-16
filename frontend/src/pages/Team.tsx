import { useState } from "react";

const SKILLS = [
  "LangGraph", "LangChain", "Neo4j", "Knowledge Graphs", "FastAPI", "RAG",
  "PyTorch", "TensorFlow", "Gemini", "LLM fine-tuning", "Docker", "Python", "SQL",
];

const TAKEAWAYS = [
  {
    head: "The semantic layer is the most important component",
    body: "Across every architecture surveyed — in-context, fine-tuned, agentic, RL — pipeline quality hinges on the semantic layer. This finding is the reason PeakSQL exists.",
  },
  {
    head: "Grounding beats scale",
    body: "Accuracy gains come from grounding models in schema and instance data, retrieval, and execution feedback — not from model size alone.",
  },
  {
    head: "Schema linking & value grounding are the failure modes",
    body: "Models misalign user language with tables/columns and assign values to the wrong fields — exactly the errors a knowledge graph of synonyms, relationships and metrics prevents.",
  },
  {
    head: "Enterprise adoption hinges on privacy, validation & cost",
    body: "On-prem deployments, small specialist models for sensitive stages, deterministically validatable outputs, and cost-aware inference are what move text-to-SQL into production.",
  },
];

export default function Team() {
  const [photoOk, setPhotoOk] = useState(true);

  return (
    <div className="page team-page">
      <section className="section">
        <h2 className="landing-h2">The team</h2>
        <p className="section-sub">PeakSQL is built end-to-end — research, architecture, agents and product — by one person who cares a lot about grounded AI systems.</p>

        <div className="team-card">
          <div className="team-left">
            {photoOk ? (
              <img
                className="avatar"
                src="/team/shikhar.jpg"
                alt="Shikhar Dave"
                onError={() => setPhotoOk(false)}
              />
            ) : (
              <div className="avatar fallback">SD</div>
            )}
            <div className="team-links">
              <a href="https://www.linkedin.com/in/shikhar-dave-400810258/" target="_blank" rel="noreferrer">
                LinkedIn ↗
              </a>
              <a href="https://github.com/shikhar5647" target="_blank" rel="noreferrer">
                GitHub ↗
              </a>
              <a href="mailto:b22ch032@iitj.ac.in">b22ch032@iitj.ac.in</a>
            </div>
          </div>

          <div className="team-body">
            <h3>Shikhar Dave</h3>
            <div className="team-role">AI Research Engineer @ Domyn · Founder & Builder, PeakSQL</div>

            <p>
              Shikhar is an <b>AI Research Engineer at Domyn</b>, where he works on text-to-SQL and
              agentic AI research — including co-authoring a comprehensive survey of the field (below)
              whose central finding, <i>the semantic layer is what makes or breaks text-to-SQL</i>,
              is the thesis PeakSQL is built on.
            </p>
            <p>
              He graduated from <b>IIT Jodhpur</b> (B.Tech in Chemical Engineering with a Minor in AI,
              Class of 2026), where he won the <b>Director's Award for the institute's best innovative
              projects</b>. Before Domyn, as a Data Science & GenAI Intern at <b>Neural Web</b> he
              contributed to 20+ GenAI projects — LangGraph multi-agent pipelines, Text2SQL systems,
              LLM fine-tuning with guardrails — and at <b>ICICI Bank</b> he built a production-ready
              multi-agent pipeline turning Account Aggregator transaction data into AI-powered
              financial insight reports used by banking teams.
            </p>
            <p>
              He led <b>MediGraphRAG</b>, a GraphRAG system over patient knowledge graphs
              (LangGraph + ArangoDB + cuGraph), and secured <b>5th place at Inter IIT Tech Meet 13.0
              (IIT Bombay)</b> with a dynamic agentic-RAG system over live-streaming data. His research
              work includes a severity-aware hierarchical classifier combining BERT with graph
              attention networks over a Neo4j knowledge graph, and he writes technical deep-dives on
              Medium about agent architectures — context engineering, long-term agent memory, and
              hierarchical reasoning models.
            </p>

            <div className="chips">
              {SKILLS.map((s) => (
                <span className="chip-tag" key={s}>
                  {s}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── The research behind PeakSQL ── */}
        <div className="paper-card">
          <div className="paper-tag">📄 Research · survey paper</div>
          <h3 className="paper-title">
            Reimagining Text-to-SQL: A Survey of Large Language Model Architectures and Strategies
          </h3>
          <div className="paper-meta">
            Shikhar Dave, Bhaskarjit Sarmah, Stefano Pasquali · Domyn · 97+ papers surveyed (2022–2025)
          </div>
          <p className="paper-abstract">
            A systematic review of LLM-driven text-to-SQL — spanning in-context learning, supervised
            and parameter-efficient fine-tuning, reinforcement learning and reasoning models, modular
            frameworks, and agentic systems — organized in a unified taxonomy by model granularity,
            level of supervision, and reasoning style, with analysis of benchmarks (Spider, Spider 2.0,
            BIRD), evaluation practice, and responsible-AI considerations for deployment.
          </p>
          <div className="takeaway-grid">
            {TAKEAWAYS.map((t) => (
              <div className="takeaway" key={t.head}>
                <div className="tk-head">{t.head}</div>
                <div className="tk-body">{t.body}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="quote-card">
          "Text-to-SQL fails when the model has to guess what your data means. PeakSQL exists so it
          never has to guess — the semantic layer is the product."
          <div className="quote-by">— Shikhar, on why PeakSQL</div>
        </div>
      </section>
    </div>
  );
}
