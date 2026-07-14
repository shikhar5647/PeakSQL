/** Minimal collapsible JSON viewer — used for full agent outputs. */
export default function JsonTree({ data, name, depth = 0 }: { data: any; name?: string; depth?: number }) {
  const label = name !== undefined ? <span className="k">{name}: </span> : null;

  if (data === null || data === undefined)
    return <div className="row">{label}<span className="b">null</span></div>;
  if (typeof data === "string")
    return <div className="row">{label}<span className="s">"{data.length > 300 ? data.slice(0, 300) + "…" : data}"</span></div>;
  if (typeof data === "number")
    return <div className="row">{label}<span className="n">{String(data)}</span></div>;
  if (typeof data === "boolean")
    return <div className="row">{label}<span className="b">{String(data)}</span></div>;

  const entries: [string, any][] = Array.isArray(data)
    ? data.map((v, i) => [String(i), v])
    : Object.entries(data);
  const preview = Array.isArray(data) ? `[${data.length}]` : `{${entries.length}}`;

  return (
    <details open={depth < 2 && entries.length <= 25}>
      <summary>{label}<span className="n">{preview}</span></summary>
      {entries.map(([k, v]) => (
        <JsonTree key={k} name={k} data={v} depth={depth + 1} />
      ))}
    </details>
  );
}
