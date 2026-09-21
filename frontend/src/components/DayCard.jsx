import { CloudRainIcon, SunIcon, AlertIcon } from "./icons";
import "./DayCard.css";

const DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  if (Number.isNaN(d.getTime())) return iso;
  return `${DAY_LABELS[d.getDay()]} · ${d.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`;
}

export default function DayCard({ day }) {
  const weather = day.weather;
  const isRainy = weather && (weather.condition || "").toLowerCase().includes("rain");

  return (
    <div className="day-card">
      <div className="day-rail">
        <span className="day-number">{String(day.day_number).padStart(2, "0")}</span>
        <span className="day-date">{formatDate(day.date)}</span>
        {weather?.forecast_available && (
          <span className={`day-weather ${isRainy ? "rainy" : "sunny"}`}>
            {isRainy ? <CloudRainIcon width={13} height={13} /> : <SunIcon width={13} height={13} />}
            {Math.round(weather.temperature_max ?? weather.temperature_min ?? 0)}°
          </span>
        )}
      </div>
      <div className="day-perforation" />
      <div className="day-activities">
        {day.activities.length === 0 && <p className="day-empty">Nothing scheduled yet.</p>}
        {day.activities.map((a, i) => (
          <div className="activity" key={a.place_id || i}>
            <span className="activity-time">{a.start_time}</span>
            <div className="activity-body">
              <span className="activity-name">{a.name}</span>
              {a.category && <span className="activity-category">{a.category}</span>}
              {a.weather_warning && (
                <span className="activity-warning">
                  <AlertIcon width={12} height={12} />
                  {a.weather_warning}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
