import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { KG } from "../types";

const LABEL_COLORS: Record<string, string> = {
  Database: "var(--ink-2)",
  Table: "var(--phase-1)",
  Column: "var(--phase-2)",
  BusinessConcept: "var(--phase-3)",
  Metric: "var(--phase-4)",
  Synonym: "var(--phase-5)",
  QueryPattern: "var(--seq-300)",
};

/** KG summary: stat tiles per node label, a schema-level graph (tables +
 *  discovered relationships), and the semantic relationship cards. */
export default function KGView({ runId, ready }: { runId: string; ready: boolean }) {
  const [kg, setKg] = useState<KG | null>(null);

  useEffect(() => {
    setKg(null);
    if (ready) api.kg(runId).then(setKg).catch(() => setKg(null));
  }, [runId, ready]);

  if (!ready) return <div className="empty">The knowledge graph appears after Agent 12 builds it.</div>;
  if (!kg) return <div className="empty">Loading knowledge graph…</div>;

  const counts: Record<string, number> = {};
  for (const n of kg.nodes) counts[n.label] = (counts[n.label] ?? 0) + 1;

  return (
    <div>
      <div className="tiles">
        <div className="tile">
          <div className="v">{kg.nodes.length}</div>
          <div className="l">nodes</div>
        </div>
        <div className="tile">
          <div className="v">{kg.relationships.length}</div>
          <div className="l">relationships</div>
        </div>
        {Object.entries(counts).map(([label, n]) => (
          <div className="tile" key={label}>
            <div className="v">{n}</div>
            <div className="l">
              <span className="swatch" style={{ background: LABEL_COLORS[label] ?? "var(--muted)" }} />
              {label}
            </div>
          </div>
        ))}
      </div>

      <div className="kg-grid">
        <div>
          <h2 className="section">Schema graph — tables & discovered relationships</h2>
          <SchemaGraph kg={kg} />
        </div>
        <div>
          <h2 className="section">Semantic relationships (Agent 8)</h2>
          <RelationshipCards kg={kg} />
        </div>
      </div>
    </div>
  );
}

function SchemaGraph({ kg }: { kg: KG }) {
  const { tables, edges } = useMemo(() => {
    const tables = kg.nodes.filter((n) => n.label === "Table").map((n) => n.properties.name as string);
    const colTable = new Map<string, string>();
    for (const n of kg.nodes)
      if (n.label === "Column") colTable.set(n.id, n.properties.table as string);
    const edges = kg.relationships
      .filter((r) => r.type === "FOREIGN_KEY" || r.type === "IMPLICIT_RELATION")
      .map((r) => ({
        from: colTable.get(r.source)!,
        to: colTable.get(r.target)!,
        implicit: r.type === "IMPLICIT_RELATION",
        meaning: (r.properties.business_meaning as string) ?? "",
        join: (r.properties.join_condition as string) ?? "",
      }))
      .filter((e) => e.from && e.to);
    return { tables, edges };
  }, [kg]);

  const W = 480;
  const H = Math.max(320, 90 + tables.length * 44);
  const cx = W / 2;
  const cy = H / 2;
  const R = Math.min(W, H) / 2 - 70;
  const pos = new Map(
    tables.map((t, i) => {
      const angle = (2 * Math.PI * i) / tables.length - Math.PI / 2;
      return [t, { x: cx + R * Math.cos(angle), y: cy + R * Math.sin(angle) }];
    }),
  );

  return (
    <svg className="schema-svg" width={W} height={H} style={{ maxWidth: "100%" }}>
      {edges.map((e, i) => {
        const a = pos.get(e.from)!;
        const b = pos.get(e.to)!;
        return (
          <g key={i}>
            <line
              x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={e.implicit ? "var(--phase-3)" : "#52514e"}
              strokeWidth={2}
              strokeDasharray={e.implicit ? "5 5" : undefined}
            >
              <title>{e.join}{e.meaning ? ` — ${e.meaning}` : ""}</title>
            </line>
          </g>
        );
      })}
      {tables.map((t) => {
        const p = pos.get(t)!;
        return (
          <g key={t}>
            <circle cx={p.x} cy={p.y} r={9} fill="var(--phase-1)" stroke="var(--surface)" strokeWidth={2} />
            <text x={p.x} y={p.y - 15} textAnchor="middle" fontSize={12} fill="var(--ink-2)">
              {t}
            </text>
          </g>
        );
      })}
      <g fontSize={11} fill="var(--muted)">
        <line x1={12} y1={H - 30} x2={40} y2={H - 30} stroke="#52514e" strokeWidth={2} />
        <text x={46} y={H - 26}>declared FK</text>
        <line x1={130} y1={H - 30} x2={158} y2={H - 30} stroke="var(--phase-3)" strokeWidth={2} strokeDasharray="5 5" />
        <text x={164} y={H - 26}>discovered (implicit)</text>
      </g>
    </svg>
  );
}

function RelationshipCards({ kg }: { kg: KG }) {
  const rels = kg.relationships.filter((r) => r.type === "FOREIGN_KEY" || r.type === "IMPLICIT_RELATION");
  if (rels.length === 0) return <div className="empty">No data relationships found.</div>;
  return (
    <div className="rel-list">
      {rels.map((r) => (
        <div className="rel-card" key={r.id}>
          <div className="join">{r.properties.join_condition}</div>
          <div className="meaning">{r.properties.business_meaning}</div>
          <div className="tags">
            <span className="badge">{r.properties.semantic_type}</span>
            <span className="badge">{r.properties.cardinality}</span>
            <span className="badge">
              {r.type === "FOREIGN_KEY" ? "declared" : "discovered"} · conf {Number(r.properties.confidence ?? 1).toFixed(2)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
