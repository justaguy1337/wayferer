import { useMemo, useState } from "react";
import "./BudgetTrendChart.css";

const WIDTH = 320;
const HEIGHT = 140;
const PAD_LEFT = 40;
const PAD_RIGHT = 14;
const PAD_TOP = 14;
const PAD_BOTTOM = 22;

function fmt(n) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);
}

function niceMax(value) {
  if (value <= 0) return 1000;
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const normalized = value / magnitude;
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return step * magnitude;
}

export default function BudgetTrendChart({ budget, numDays, onExpand, expandable = true }) {
  const [hoverIdx, setHoverIdx] = useState(null);

  const { points, labels, maxY, budgetLine } = useMemo(() => {
    const b = budget.breakdown || {};
    const days = Math.max(numDays || 1, 1);
    const upfront = (b.flights || 0) + (b.hotels || 0);
    const perDay = ((b.food || 0) + (b.transport || 0) + (b.activities || 0) + (b.miscellaneous || 0)) / days;

    const cumulative = [upfront];
    for (let i = 1; i <= days; i++) cumulative.push(cumulative[i - 1] + perDay);

    const labels = ["Pre-trip", ...Array.from({ length: days }, (_, i) => `Day ${i + 1}`)];
    const ceiling = budget.total_budget || 0;
    const maxRaw = Math.max(...cumulative, ceiling);
    const maxY = niceMax(maxRaw * 1.1);

    const innerW = WIDTH - PAD_LEFT - PAD_RIGHT;
    const innerH = HEIGHT - PAD_TOP - PAD_BOTTOM;
    const n = cumulative.length;
    const points = cumulative.map((v, i) => ({
      x: PAD_LEFT + (n === 1 ? 0 : (i / (n - 1)) * innerW),
      y: PAD_TOP + innerH - (v / maxY) * innerH,
      value: v,
    }));

    const budgetLine = ceiling ? PAD_TOP + innerH - (ceiling / maxY) * innerH : null;

    return { points, labels, maxY, budgetLine };
  }, [budget, numDays]);

  if (points.length < 2) return null;

  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${HEIGHT - PAD_BOTTOM} L ${points[0].x} ${HEIGHT - PAD_BOTTOM} Z`;
  const hover = hoverIdx != null ? points[hoverIdx] : null;

  return (
    <div
      className={`budget-trend ${expandable ? "clickable" : ""}`}
      onClick={expandable ? onExpand : undefined}
      role={expandable ? "button" : undefined}
      tabIndex={expandable ? 0 : undefined}
      title={expandable ? "Click to see full trip dashboard" : undefined}
    >
      <div className="budget-trend-head">
        <span className="budget-trend-title">Spend over the trip</span>
        {expandable && <span className="budget-trend-hint">Click to expand ↗</span>}
      </div>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="budget-trend-svg"
        onMouseLeave={() => setHoverIdx(null)}
      >
        {[0, 0.5, 1].map((t) => (
          <line
            key={t}
            x1={PAD_LEFT}
            x2={WIDTH - PAD_RIGHT}
            y1={PAD_TOP + t * (HEIGHT - PAD_TOP - PAD_BOTTOM)}
            y2={PAD_TOP + t * (HEIGHT - PAD_TOP - PAD_BOTTOM)}
            className="budget-trend-grid"
          />
        ))}
        {budgetLine != null && (
          <>
            <line x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT} y1={budgetLine} y2={budgetLine} className="budget-trend-ceiling" />
            <text x={WIDTH - PAD_RIGHT} y={budgetLine - 4} className="budget-trend-ceiling-label" textAnchor="end">
              Budget ₹{fmt(budget.total_budget)}
            </text>
          </>
        )}
        <path d={areaPath} className="budget-trend-area" />
        <path d={linePath} className="budget-trend-line" />
        {points.map((p, i) => (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={i === hoverIdx ? 5 : 3.5}
            className="budget-trend-dot"
            onMouseEnter={(e) => {
              e.stopPropagation();
              setHoverIdx(i);
            }}
          />
        ))}
        {hover && (
          <line x1={hover.x} x2={hover.x} y1={PAD_TOP} y2={HEIGHT - PAD_BOTTOM} className="budget-trend-crosshair" />
        )}
      </svg>
      <div className="budget-trend-labels">
        <span>{labels[0]}</span>
        <span>{labels[labels.length - 1]}</span>
      </div>
      {hover && (
        <div className="budget-trend-tooltip">
          {labels[hoverIdx]}: <strong>₹{fmt(Math.round(hover.value))}</strong>
        </div>
      )}
    </div>
  );
}
