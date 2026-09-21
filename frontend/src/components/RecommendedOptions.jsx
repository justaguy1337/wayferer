import "./RecommendedOptions.css";

function fmt(n) {
  if (n == null) return "";
  const num = typeof n === "string" ? parseFloat(n) : n;
  if (Number.isNaN(num)) return n;
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(num);
}

function FlightRow({ flight }) {
  const first = flight.itineraries?.[0]?.segments?.[0];
  const route = first ? `${first.from} → ${first.to}` : null;
  const stops = flight.itineraries?.[0]?.stops;
  return (
    <a className="rec-row" href={flight.redirect_url} target="_blank" rel="noopener noreferrer">
      <div className="rec-row-main">
        <span className="rec-row-title">{route || "Flight option"}</span>
        <span className="rec-row-meta">
          {first?.carrier}
          {stops != null && ` · ${stops === 0 ? "Nonstop" : `${stops} stop${stops > 1 ? "s" : ""}`}`}
        </span>
      </div>
      <span className="rec-row-price">
        {flight.currency} {fmt(flight.price)}
      </span>
    </a>
  );
}

function HotelRow({ hotel }) {
  return (
    <a className="rec-row" href={hotel.redirect_url || hotel.source_url} target="_blank" rel="noopener noreferrer">
      <div className="rec-row-main">
        <span className="rec-row-title">{hotel.name}</span>
        {hotel.summary && <span className="rec-row-meta">{hotel.summary.slice(0, 70)}...</span>}
      </div>
      <span className="rec-row-arrow">↗</span>
    </a>
  );
}

export default function RecommendedOptions({ flights, hotels, layout = "column" }) {
  if ((!flights || flights.length === 0) && (!hotels || hotels.length === 0)) return null;

  const hotelGroup = hotels && hotels.length > 0 && (
    <div className="recommended-group">
      <span className="recommended-title">Recommended hotels</span>
      {hotels.map((h, i) => (
        <HotelRow key={h.name + i} hotel={h} />
      ))}
    </div>
  );

  const flightGroup = flights && flights.length > 0 && (
    <div className="recommended-group">
      <span className="recommended-title">Recommended flights</span>
      {flights.map((f, i) => (
        <FlightRow key={f.id || i} flight={f} />
      ))}
    </div>
  );

  return (
    <div className={`recommended recommended-${layout}`}>
      {hotelGroup}
      {flightGroup}
    </div>
  );
}
