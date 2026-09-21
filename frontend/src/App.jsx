import { useEffect, useRef, useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";
import ItineraryPanel from "./components/ItineraryPanel";
import TripDashboard from "./components/TripDashboard";
import { api, streamChat } from "./api";
import "./App.css";

let keyCounter = 0;
const nextKey = () => `activity-${++keyCounter}`;

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [itinerary, setItinerary] = useState(null);
  const [budget, setBudget] = useState(null);
  const [flightOptions, setFlightOptions] = useState(null);
  const [hotelOptions, setHotelOptions] = useState(null);
  const [pending, setPending] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [pendingConfirm, setPendingConfirm] = useState(null);
  const [tripSummary, setTripSummary] = useState(null);
  const [showDashboard, setShowDashboard] = useState(false);
  const revealTimer = useRef(null);
  const didInit = useRef(false);
  const pendingRef = useRef(null);

  useEffect(() => {
    pendingRef.current = pending;
  }, [pending]);

  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;
    (async () => {
      const list = await api.listSessions();
      if (list.length === 0) {
        const created = await api.createSession("New trip");
        setSessions([created]);
        setActiveId(created.id);
      } else {
        setSessions(list);
        await loadSession(list[0].id);
      }
    })().catch((e) => setError(e.message));
    return () => clearInterval(revealTimer.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadSession(id) {
    const detail = await api.getSession(id);
    setActiveId(id);
    setMessages(detail.messages.map((m) => ({ role: m.role, content: m.content })));
    setItinerary(detail.itinerary);
    setBudget(detail.budget);
    setFlightOptions(detail.flight_options);
    setHotelOptions(detail.hotel_options);
    setTripSummary(detail.trip_summary);
    setPending(null);
    setPendingConfirm(null);
    setShowDashboard(false);
  }

  async function handleCreate() {
    const created = await api.createSession("New trip");
    setSessions((s) => [created, ...s]);
    setActiveId(created.id);
    setMessages([]);
    setItinerary(null);
    setBudget(null);
    setFlightOptions(null);
    setHotelOptions(null);
    setTripSummary(null);
    setPending(null);
    setPendingConfirm(null);
  }

  async function handleSelect(id) {
    if (id === activeId || isStreaming) return;
    await loadSession(id).catch((e) => setError(e.message));
  }

  async function handleRename(id, title) {
    await api.renameSession(id, title);
    setSessions((s) => s.map((sess) => (sess.id === id ? { ...sess, title } : sess)));
  }

  async function handleDelete(id) {
    await api.deleteSession(id);
    const remaining = sessions.filter((s) => s.id !== id);
    setSessions(remaining);
    if (id === activeId) {
      if (remaining.length > 0) {
        await loadSession(remaining[0].id);
      } else {
        const created = await api.createSession("New trip");
        setSessions([created]);
        await loadSession(created.id);
      }
    }
  }

  function markLastRunningDone() {
    setPending((p) => {
      if (!p) return p;
      const idx = [...p.activities].reverse().findIndex((a) => a.status === "running");
      if (idx === -1) return p;
      const realIdx = p.activities.length - 1 - idx;
      const activities = p.activities.slice();
      activities[realIdx] = { ...activities[realIdx], status: "done" };
      return { ...p, activities };
    });
  }

  function revealText(fullText, activityLabels) {
    clearInterval(revealTimer.current);
    let i = 0;
    const step = Math.max(2, Math.ceil(fullText.length / 60));
    revealTimer.current = setInterval(() => {
      i += step;
      const slice = fullText.slice(0, i);
      setPending((p) => (p ? { ...p, text: slice } : p));
      if (i >= fullText.length) {
        clearInterval(revealTimer.current);
        setMessages((m) => [...m, { role: "assistant", content: fullText, activities: activityLabels }]);
        setPending(null);
        setIsStreaming(false);
        setSessions((s) => {
          const updated = s.find((x) => x.id === activeId);
          if (!updated) return s;
          const rest = s.filter((x) => x.id !== activeId);
          return [{ ...updated, updated_at: Date.now() / 1000 }, ...rest];
        });
      }
    }, 12);
  }

  async function sendToAgent(sessionId, text, force) {
    setPending({ activities: [], text: "" });
    setIsStreaming(true);

    try {
      await streamChat(
        sessionId,
        text,
        (event) => {
          if (event.type === "tool_start") {
            setPending((p) => (p ? { ...p, activities: [...p.activities, { key: nextKey(), label: event.label, status: "running" }] } : p));
          } else if (event.type === "tool_end") {
            markLastRunningDone();
          } else if (event.type === "itinerary_update") {
            setItinerary(event.itinerary);
          } else if (event.type === "budget_update") {
            setBudget(event.budget);
          } else if (event.type === "flight_options") {
            setFlightOptions(event.options);
          } else if (event.type === "hotel_options") {
            setHotelOptions(event.options);
          } else if (event.type === "confirm_new_trip") {
            setPending(null);
            setIsStreaming(false);
            setPendingConfirm({ message: text, currentDestination: event.current_destination });
          } else if (event.type === "token") {
            const p = pendingRef.current;
            const labels = p ? p.activities.filter((a) => a.status === "done").map((a) => a.label) : [];
            revealText(event.content, labels);
          } else if (event.type === "error") {
            setError(event.message);
            setPending(null);
            setIsStreaming(false);
          }
        },
        undefined,
        force
      );
    } catch (e) {
      setError(e.message);
      setPending(null);
      setIsStreaming(false);
    }
  }

  async function handleSend(text) {
    if (!activeId || isStreaming) return;
    setError(null);
    setMessages((m) => [...m, { role: "user", content: text }]);
    await sendToAgent(activeId, text, false);
  }

  async function resolveNewTripConfirm(startNew) {
    const { message } = pendingConfirm;
    setPendingConfirm(null);
    if (startNew) {
      const created = await api.createSession("New trip");
      setSessions((s) => [created, ...s]);
      setActiveId(created.id);
      setMessages([{ role: "user", content: message }]);
      setItinerary(null);
      setBudget(null);
      setFlightOptions(null);
      setHotelOptions(null);
      setTripSummary(null);
      await sendToAgent(created.id, message, false);
    } else {
      await sendToAgent(activeId, message, true);
    }
  }

  return (
    <div className="app-shell">
      <Sidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={handleSelect}
        onCreate={handleCreate}
        onRename={handleRename}
        onDelete={handleDelete}
      />
      <ChatPanel
        messages={messages}
        pending={pending}
        onSend={handleSend}
        disabled={isStreaming || !activeId}
        pendingConfirm={pendingConfirm}
        onResolveConfirm={resolveNewTripConfirm}
      />
      <ItineraryPanel
        itinerary={itinerary}
        budget={budget}
        flightOptions={flightOptions}
        hotelOptions={hotelOptions}
        onOpenDashboard={() => setShowDashboard(true)}
      />
      {showDashboard && (
        <TripDashboard
          itinerary={itinerary}
          budget={budget}
          flightOptions={flightOptions}
          hotelOptions={hotelOptions}
          tripSummary={tripSummary}
          onClose={() => setShowDashboard(false)}
        />
      )}
      {error && (
        <div className="error-toast" onClick={() => setError(null)}>
          {error}
        </div>
      )}
    </div>
  );
}
