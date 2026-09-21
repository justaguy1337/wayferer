import "./ActivityFeed.css";

export default function ActivityFeed({ items }) {
  if (!items.length) return null;

  return (
    <div className="activity-board" role="status" aria-live="polite">
      {items.map((item) => (
        <div key={item.key} className={`activity-row ${item.status}`}>
          <span className="activity-dot" />
          <span className="activity-label">{item.label}</span>
        </div>
      ))}
    </div>
  );
}
