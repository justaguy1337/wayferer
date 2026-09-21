import { MapContainer, TileLayer, CircleMarker, Popup, Polyline } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "./TripMap.css";

const DAY_COLORS = ["#e8a33d", "#4fbdb0", "#d9737c", "#7c9fd9", "#c7a3e8", "#8fd67a", "#e8d33d", "#d38fe8"];

export default function TripMap({ days }) {
  const points = [];
  days.forEach((day, di) => {
    day.activities.forEach((a) => {
      if (a.lat != null && a.lon != null) {
        points.push({ ...a, day: day.day_number, color: DAY_COLORS[di % DAY_COLORS.length] });
      }
    });
  });

  if (points.length === 0) {
    return <div className="map-empty">No located activities to show yet.</div>;
  }

  const center = [
    points.reduce((s, p) => s + p.lat, 0) / points.length,
    points.reduce((s, p) => s + p.lon, 0) / points.length,
  ];

  const byDay = {};
  points.forEach((p) => {
    byDay[p.day] = byDay[p.day] || [];
    byDay[p.day].push([p.lat, p.lon]);
  });

  return (
    <div className="map-wrap">
      <MapContainer center={center} zoom={12} scrollWheelZoom={false} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {Object.entries(byDay).map(([day, path]) => (
          <Polyline key={day} positions={path} pathOptions={{ color: DAY_COLORS[(day - 1) % DAY_COLORS.length], weight: 2, opacity: 0.5, dashArray: "4 6" }} />
        ))}
        {points.map((p, i) => (
          <CircleMarker
            key={i}
            center={[p.lat, p.lon]}
            radius={7}
            pathOptions={{ color: p.color, fillColor: p.color, fillOpacity: 0.85, weight: 1.5 }}
          >
            <Popup>
              <strong>{p.name}</strong>
              <br />
              Day {p.day} · {p.start_time}
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
