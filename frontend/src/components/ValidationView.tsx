import { useEffect, useState } from "react";
import { api } from "../api";

const SEVERITY_ICON: Record<string, string> = { critical: "🚫", warning: "⚠️", info: "ℹ️" };

/** Agent 13's gate report: completeness bars, check list, identified gaps. */
export default function ValidationView({ runId, ready }: { runId: string; ready: boolean }) {
  const [report, setReport] = useState<any>(null);

  useEffect(() => {
    setReport(null);
    if (ready)
      api.agentOutput(runId, "a13")
        .then((o) => setReport(o.validation_report))
        .catch(() => setReport(null));
  }, [runId, ready]);

  if (!ready) return <div className="empty">The validation report appears after Agent 13 runs.</div>;
  if (!report) return <div className="empty">Loading validation report…</div>;

  const scores: [string, number][] = Object.entries(report.completeness_scores ?? {}) as any;
  const quality: [string, number][] = Object.entries(report.quality_metrics ?? {}) as any;

  return (
    <div>
      <div className="agent-head">
        <h2>Validation gate</h2>
        <span className={`badge ${report.overall_status === "passed" ? "completed" : report.overall_status === "warning" ? "warning" : "failed"}`}>
          {report.overall_status.toUpperCase()}
        </span>
      </div>

      <h2 className="section">Completeness</h2>
      <div className="score-bars">
        {scores.map(([k, v]) => (
          <ScoreBar key={k} label={k.replaceAll("_", " ")} value={v} />
        ))}
      </div>

      <h2 className="section">Quality</h2>
      <div className="score-bars">
        {quality.map(([k, v]) => (
          <ScoreBar key={k} label={k.replaceAll("_", " ")} value={v} />
        ))}
      </div>

      <h2 className="section">Checks</h2>
      {report.checks.map((c: any, i: number) => (
        <div className="check-row" key={i}>
          <span>{c.status === "passed" ? "✅" : SEVERITY_ICON[c.severity] ?? "❌"}</span>
          <span className="nm">{c.check_name.replaceAll("_", " ")}</span>
          <span className="dt">{c.details}</span>
        </div>
      ))}

      {report.gaps_identified?.length > 0 && (
        <>
          <h2 className="section">Gaps for human review</h2>
          {report.gaps_identified.map((g: any, i: number) => (
            <div className="check-row" key={i}>
              <span>🔍</span>
              <span className="nm">{g.entity}</span>
              <span className="dt">{g.recommendation}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div className="score-row">
      <span className="lbl">{label}</span>
      <div className="bar">
        <div style={{ width: `${pct}%` }} />
      </div>
      <span className="val">{pct}%</span>
    </div>
  );
}
