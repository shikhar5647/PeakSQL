import { useState } from "react";

const SKILLS = [
  "LangGraph", "LangChain", "Neo4j", "Knowledge Graphs", "FastAPI", "RAG",
  "PyTorch", "TensorFlow", "Gemini", "LLM fine-tuning", "Docker", "Python", "SQL",
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
            <div className="team-role">Founder & Builder · Data Science / GenAI Engineer</div>

            <p>
              Shikhar is a final-year B.Tech student at <b>IIT Jodhpur</b> (Chemical Engineering with a
              Minor in AI, Class of 2026) who has spent the last two years building production
              generative-AI systems — including the multi-agent pipelines, Text2SQL systems and
              knowledge-graph work that PeakSQL grew out of.
            </p>
            <p>
              As a <b>Data Science & GenAI Intern at Neural Web</b>, he contributed to 20+ GenAI
              projects — LangGraph multi-agent pipelines, Text2SQL systems, LLM fine-tuning with
              guardrails, and knowledge-distillation for deployable models. At <b>ICICI Bank</b>, he
              built a production-ready multi-agent pipeline turning Account Aggregator transaction
              data into AI-powered financial insight reports used by banking teams.
            </p>
            <p>
              He led <b>MediGraphRAG</b>, a GraphRAG system over patient knowledge graphs
              (LangGraph + ArangoDB + cuGraph), and secured <b>5th place at Inter IIT Tech Meet 13.0
              (IIT Bombay)</b> with a dynamic agentic-RAG system over live-streaming data. His
              research work includes a severity-aware hierarchical classifier combining BERT with
              graph attention networks over a Neo4j knowledge graph — the same conviction that
              powers PeakSQL: <i>language models get dramatically better when they reason over
              structured knowledge instead of guessing.</i>
            </p>
            <p>
              He also writes technical deep-dives on Medium about agent architectures — context
              engineering, long-term agent memory, and hierarchical reasoning models.
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

        <div className="quote-card">
          "Text-to-SQL fails when the model has to guess what your data means. PeakSQL exists so it
          never has to guess — the semantic layer is the product."
          <div className="quote-by">— Shikhar, on why PeakSQL</div>
        </div>
      </section>
    </div>
  );
}
