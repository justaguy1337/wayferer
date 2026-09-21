import { CompassIcon } from "./icons";
import DayCard from "./DayCard";
import BudgetMeter from "./BudgetMeter";
import BudgetTrendChart from "./BudgetTrendChart";
import TripMap from "./TripMap";
import TravelSummary from "./TravelSummary";
import RecommendedOptions from "./RecommendedOptions";
import "./ItineraryPanel.css";

export default function ItineraryPanel({ itinerary, budget, flightOptions, hotelOptions, onOpenDashboard }) {
  if (!itinerary) {
    return (
      <aside className="itinerary-panel empty">
        <CompassIcon className="itinerary-empty-icon" />
        <p>Your day-by-day plan, budget and map will build up here as we chat.</p>
      </aside>
    );
  }

  return (
    <aside className="itinerary-panel">
      <div className="itinerary-header">
        <div>
          <h2>{itinerary.destination}</h2>
          <span className="itinerary-dates">
            {itinerary.start_date} → {itinerary.end_date} · {itinerary.pace} pace
          </span>
        </div>
        <button className="dashboard-btn" onClick={onOpenDashboard} title="View full trip dashboard">
          Full view
        </button>
      </div>

      <div className="itinerary-scroll">
        <TripMap days={itinerary.days} />
        <TravelSummary flight={itinerary.flight} hotel={itinerary.hotel} />
        {budget && <BudgetTrendChart budget={budget} numDays={itinerary.days.length} onExpand={onOpenDashboard} />}
        {budget && <BudgetMeter budget={budget} />}
        <RecommendedOptions flights={flightOptions} hotels={hotelOptions} />
        <div className="day-list">
          {itinerary.days.map((day) => (
            <DayCard key={day.day_number} day={day} />
          ))}
        </div>
        {itinerary.unscheduled_places?.length > 0 && (
          <div className="unscheduled">
            <span className="unscheduled-title">Not yet scheduled</span>
            {itinerary.unscheduled_places.map((p) => (
              <span key={p.place_id || p.name} className="unscheduled-chip">
                {p.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
