import "./BudgetMeter.css";

const CATEGORY_LABELS = {
  flights: "Flights",
  hotels: "Hotels",
  food: "Food",
  transport: "Transport",
  activities: "Activities",
  miscellaneous: "Misc",
};

const CATEGORY_COLORS = {
  flights: "#e8a33d",
  hotels: "#4fbdb0",
  food: "#d9737c",
  transport: "#7c9fd9",
  activities: "#c7a3e8",
  miscellaneous: "#5c6480",
};

function fmt(n) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(n);
}

export default function BudgetMeter({ budget }) {
  const { breakdown, total_spend, total_budget, over_budget, percent_used } = budget;
  const entries = Object.entries(breakdown).filter(([, v]) => v > 0);
  const max = total_budget || total_spend || 1;

  return (
    <div className="budget-card">
      <div className="budget-header">
        <span className="budget-title">Budget</span>
        <span className={`budget-total ${over_budget ? "over" : ""}`}>
          ₹{fmt(total_spend)}
          {total_budget ? ` / ₹${fmt(total_budget)}` : ""}
        </span>
      </div>

      <div className="budget-bar">
        {entries.map(([key, value]) => (
          <div
            key={key}
            className="budget-bar-segment"
            style={{ width: `${Math.min((value / max) * 100, 100)}%`, background: CATEGORY_COLORS[key] }}
            title={`${CATEGORY_LABELS[key]}: ₹${fmt(value)}`}
          />
        ))}
      </div>

      {over_budget && (
        <p className="budget-warning">Over budget by ₹{fmt(Math.abs(budget.difference))} — worth trimming something.</p>
      )}
      {!over_budget && percent_used != null && <p className="budget-note">{percent_used}% of budget used</p>}

      <div className="budget-legend">
        {entries.map(([key, value]) => (
          <div className="legend-item" key={key}>
            <span className="legend-dot" style={{ background: CATEGORY_COLORS[key] }} />
            <span className="legend-label">{CATEGORY_LABELS[key]}</span>
            <span className="legend-value">₹{fmt(value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
