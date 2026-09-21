import { PlaneIcon } from "./icons";
import "./TravelSummary.css";

const KNOWN_FLIGHT_KEYS = new Set([
  "price",
  "currency",
  "carrier",
  "airline",
  "flight_number",
  "departure_time",
  "arrival_time",
  "departure",
  "arrival",
  "origin",
  "destination",
  "stops",
  "duration",
]);

const KNOWN_HOTEL_KEYS = new Set(["name", "price", "rate", "currency", "address", "rating", "per_night"]);

function fmtValue(v) {
  if (v == null) return null;
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function humanize(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function ExtraFields({ data, known }) {
  const extras = Object.entries(data).filter(([k, v]) => !known.has(k) && v != null && fmtValue(v));
  if (extras.length === 0) return null;
  return (
    <div className="travel-extra">
      {extras.map(([k, v]) => (
        <span key={k} className="travel-extra-chip">
          <span className="travel-extra-label">{humanize(k)}:</span> {fmtValue(v)}
        </span>
      ))}
    </div>
  );
}

function FlightCard({ flight }) {
  if (!flight) return null;
  const price = flight.price ?? flight.total_amount;
  const currency = flight.currency ?? "";
  const route = [flight.origin, flight.destination].filter(Boolean).join(" → ");
  const times = [flight.departure_time ?? flight.departure, flight.arrival_time ?? flight.arrival].filter(Boolean).join(" → ");
  const carrier = flight.carrier ?? flight.airline;

  return (
    <div className="travel-card">
      <div className="travel-card-icon">
        <PlaneIcon width={16} height={16} />
      </div>
      <div className="travel-card-body">
        <div className="travel-card-head">
          <span className="travel-card-title">Flight</span>
          {price != null && (
            <span className="travel-card-price">
              {currency} {price}
            </span>
          )}
        </div>
        {route && <div className="travel-card-line">{route}</div>}
        <div className="travel-card-meta">
          {carrier && <span>{carrier}{flight.flight_number ? ` ${flight.flight_number}` : ""}</span>}
          {times && <span>{times}</span>}
          {flight.stops != null && <span>{flight.stops === 0 ? "Nonstop" : `${flight.stops} stop${flight.stops > 1 ? "s" : ""}`}</span>}
        </div>
        <ExtraFields data={flight} known={KNOWN_FLIGHT_KEYS} />
      </div>
    </div>
  );
}

function HotelCard({ hotel }) {
  if (!hotel) return null;
  const price = hotel.price ?? hotel.rate ?? hotel.per_night;
  const currency = hotel.currency ?? "";

  return (
    <div className="travel-card">
      <div className="travel-card-icon hotel">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path d="M3 21V7a1 1 0 0 1 1-1h4v15M15 21V6h5a1 1 0 0 1 1 1v14M8 21v-4h4v4M8 10h.01M8 14h.01M11 10h.01M11 14h.01M18 10h.01M18 14h.01" />
        </svg>
      </div>
      <div className="travel-card-body">
        <div className="travel-card-head">
          <span className="travel-card-title">Hotel</span>
          {price != null && (
            <span className="travel-card-price">
              {currency} {price}
            </span>
          )}
        </div>
        {hotel.name && <div className="travel-card-line">{hotel.name}</div>}
        <div className="travel-card-meta">
          {hotel.rating != null && <span>★ {hotel.rating}</span>}
          {hotel.address && <span>{hotel.address}</span>}
        </div>
        <ExtraFields data={hotel} known={KNOWN_HOTEL_KEYS} />
      </div>
    </div>
  );
}

export default function TravelSummary({ flight, hotel }) {
  if (!flight && !hotel) return null;
  return (
    <div className="travel-summary">
      <FlightCard flight={flight} />
      <HotelCard hotel={hotel} />
    </div>
  );
}
