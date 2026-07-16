/** Animated hero background: a knowledge-graph constellation whose signals
 *  converge into SQL, run against the database, and return result rows.
 *  Pure SVG + SMIL — no JS animation loop; hidden under prefers-reduced-motion. */

const NODE_COLORS = ["#3987e5", "#6da7ec", "#9085e9", "#199e70", "#d55181"];

// twinkling constellation spread across the whole hero (kept faint — copy sits above)
const NODES: [number, number, number][] = [
  // [x, y, r]
  [90, 70, 3], [230, 150, 4], [400, 60, 3], [560, 130, 3.5], [720, 55, 3],
  [880, 140, 4], [1050, 70, 3], [1210, 150, 3.5], [1360, 80, 3],
  [150, 280, 3.5], [330, 330, 3], [520, 260, 4], [700, 320, 3],
  [980, 290, 3.5], [1150, 330, 3], [1320, 260, 4],
  [60, 430, 3], [260, 470, 3.5], [450, 420, 3],
];

const LINKS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8],
  [1, 9], [9, 10], [10, 11], [11, 3], [11, 12], [12, 5], [12, 13],
  [13, 14], [14, 15], [15, 8], [9, 16], [16, 17], [17, 18], [18, 10],
  [13, 7], [2, 11],
];

// the story band along the bottom: cluster → SQL → DB → results
const CLUSTER: [number, number][] = [[150, 490], [230, 455], [310, 500], [250, 540], [190, 525]];
const CLUSTER_LINKS: [number, number][] = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0], [1, 3], [0, 2]];

const CONVERGE = [
  "M310 500 C 420 500, 500 492, 596 492",
  "M230 455 C 400 448, 500 480, 596 486",
  "M250 540 C 420 545, 510 505, 596 498",
];

export default function HeroConstellation() {
  return (
    <div className="hero-anim" aria-hidden>
      <svg viewBox="0 0 1440 620" width="100%" height="100%" preserveAspectRatio="xMidYMid slice">
        {/* ── faint constellation across the hero ── */}
        <g opacity="0.5">
          {LINKS.map(([a, b], i) => (
            <line
              key={i}
              x1={NODES[a][0]} y1={NODES[a][1]} x2={NODES[b][0]} y2={NODES[b][1]}
              stroke="#3987e5" strokeOpacity="0.14" strokeWidth="1"
            />
          ))}
          {NODES.map(([x, y, r], i) => (
            <circle key={i} cx={x} cy={y} r={r} fill={NODE_COLORS[i % NODE_COLORS.length]}>
              <animate
                attributeName="opacity" values="0.25;0.85;0.25" dur={`${3.5 + (i % 5)}s`}
                begin={`${-(i * 0.7)}s`} repeatCount="indefinite"
              />
            </circle>
          ))}
          {/* a few pulses wandering the constellation */}
          {[[0, 1], [11, 12], [13, 14], [9, 10], [3, 4]].map(([a, b], i) => (
            <circle key={`p${i}`} r="2.2" fill="#6da7ec" opacity="0.8">
              <animateMotion
                dur={`${4 + i}s`} begin={`${-i * 1.6}s`} repeatCount="indefinite"
                path={`M${NODES[a][0]} ${NODES[a][1]} L${NODES[b][0]} ${NODES[b][1]}`}
              />
            </circle>
          ))}
        </g>

        {/* ── the story band: KG → SQL → DB → results ── */}
        <g opacity="0.75">
          {/* mini knowledge-graph cluster */}
          {CLUSTER_LINKS.map(([a, b], i) => (
            <line
              key={i}
              x1={CLUSTER[a][0]} y1={CLUSTER[a][1]} x2={CLUSTER[b][0]} y2={CLUSTER[b][1]}
              stroke="#6da7ec" strokeOpacity="0.3" strokeWidth="1.2"
            />
          ))}
          {CLUSTER.map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={4} fill={NODE_COLORS[i % NODE_COLORS.length]}>
              <animate attributeName="opacity" values="0.5;1;0.5" dur="3s" begin={`${-i}s`} repeatCount="indefinite" />
            </circle>
          ))}

          {/* convergence paths + traveling signals */}
          {CONVERGE.map((d, i) => (
            <g key={i}>
              <path d={d} fill="none" stroke="#3987e5" strokeOpacity="0.18" strokeWidth="1.2" strokeDasharray="3 5" />
              <circle r="3" fill="#3987e5">
                <animateMotion dur="2.8s" begin={`${-i * 0.9}s`} repeatCount="indefinite" path={d} />
                <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.15;0.85;1" dur="2.8s" begin={`${-i * 0.9}s`} repeatCount="indefinite" />
              </circle>
            </g>
          ))}

          {/* SQL chip */}
          <rect x={600} y={468} width={78} height={44} rx={10} fill="rgba(57,135,229,0.10)" stroke="rgba(57,135,229,0.5)">
            <animate attributeName="stroke-opacity" values="0.3;0.8;0.3" dur="2.8s" repeatCount="indefinite" />
          </rect>
          <text x={639} y={496} textAnchor="middle" fontFamily="ui-monospace, Menlo, monospace" fontSize="16" fontWeight="700" fill="#6da7ec">
            SQL
            <animate attributeName="opacity" values="0.6;1;0.6" dur="2.8s" repeatCount="indefinite" />
          </text>

          {/* SQL → DB */}
          <path id="sql-db" d="M678 490 L 848 490" fill="none" stroke="#9085e9" strokeOpacity="0.22" strokeWidth="1.2" strokeDasharray="3 5" />
          <circle r="3" fill="#9085e9">
            <animateMotion dur="1.8s" repeatCount="indefinite" path="M678 490 L 848 490" />
          </circle>

          {/* database cylinder */}
          <g stroke="rgba(144,133,233,0.55)" fill="rgba(144,133,233,0.08)">
            <path d="M852 472 v36 a34 11 0 0 0 68 0 v-36" />
            <ellipse cx={886} cy={472} rx={34} ry={11}>
              <animate attributeName="stroke-opacity" values="0.35;0.85;0.35" dur="2.4s" repeatCount="indefinite" />
            </ellipse>
          </g>

          {/* DB → results */}
          {[476, 490, 504].map((y, i) => (
            <g key={i}>
              <path d={`M922 ${y} L 1042 ${y}`} fill="none" stroke="#199e70" strokeOpacity="0.18" strokeWidth="1" strokeDasharray="2 5" />
              <circle r="2.4" fill="#199e70">
                <animateMotion dur="1.6s" begin={`${-i * 0.5}s`} repeatCount="indefinite" path={`M922 ${y} L 1042 ${y}`} />
              </circle>
            </g>
          ))}

          {/* result rows lighting up */}
          {[[1050, 462, 150], [1050, 480, 118], [1050, 498, 136], [1050, 516, 96]].map(([x, y, w], i) => (
            <rect key={i} x={x} y={y} width={w} height={10} rx={3} fill="#199e70">
              <animate
                attributeName="opacity" values="0.08;0.5;0.5;0.08" keyTimes="0;0.2;0.8;1"
                dur="4.5s" begin={`${i * 0.45}s`} repeatCount="indefinite"
              />
            </rect>
          ))}
          {/* tiny bar chart */}
          {[[1240, 26], [1258, 44], [1276, 16], [1294, 36]].map(([x, h], i) => (
            <rect key={i} x={x} y={526 - h} width={11} height={h} rx={3} fill="#3987e5">
              <animate
                attributeName="opacity" values="0.12;0.55;0.12" dur="3.6s" begin={`${-i * 0.8}s`} repeatCount="indefinite"
              />
            </rect>
          ))}
        </g>
      </svg>
    </div>
  );
}
