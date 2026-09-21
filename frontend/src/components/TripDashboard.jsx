import DayCard from "./DayCard";
import BudgetMeter from "./BudgetMeter";
import BudgetTrendChart from "./BudgetTrendChart";
import TripMap from "./TripMap";
import TravelSummary from "./TravelSummary";
import RecommendedOptions from "./RecommendedOptions";
import "./TripDashboard.css";

export default function TripDashboard({ itinerary, budget, flightOptions, hotelOptions, tripSummary, onClose }) {
  if (!itinerary) return null;

  return (
    <div className="dashboard-overlay" role="dialog" aria-modal="true">
      <div className="dashboard-backdrop" onClick={onClose} />
      <div className="dashboard-panel">
        <div className="dashboard-header">
          <div>
            <h1>{itinerary.destination}</h1>
            <span className="dashboard-dates">
              {itinerary.start_date} → {itinerary.end_date} · {itinerary.pace} pace
            </span>
          </div>
          <button className="dashboard-close" onClick={onClose} title="Close dashboard">
            ✕
          </button>
        </div>

        {tripSummary && (
          <div className="dashboard-summary">
            <span className="dashboard-summary-label">Trip summary</span>
            <p>{tripSummary}</p>
          </div>
        )}

        <div className="dashboard-grid">
          <div className="dashboard-col">
            <TripMap days={itinerary.days} />
            <div className="dashboard-days">
              {itinerary.days.map((day) => (
                <DayCard key={day.day_number} day={day} />
              ))}
            </div>
          </div>

          <div className="dashboard-col">
            <TravelSummary flight={itinerary.flight} hotel={itinerary.hotel} />
            {budget && <BudgetTrendChart budget={budget} numDays={itinerary.days.length} expandable={false} />}
            {budget && <BudgetMeter budget={budget} />}
            <RecommendedOptions flights={flightOptions} hotels={hotelOptions} layout="row" />
          </div>
        </div>
      </div>
    </div>
  );
}
