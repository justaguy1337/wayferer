import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import ActivityFeed from "./ActivityFeed";
import Composer from "./Composer";
import { PlaneIcon } from "./icons";
import "./ChatPanel.css";

function Bubble({ role, content, activities }) {
  const isUser = role === "user";
  return (
    <div className={`bubble-row ${isUser ? "user" : "assistant"}`}>
      <div className="bubble">
        {!isUser && activities && activities.length > 0 && (
          <div className="bubble-trail">
            {activities.map((a, i) => (
              <span key={i} className="trail-chip">
                {a}
              </span>
            ))}
          </div>
        )}
        {isUser ? (
          <p className="bubble-text">{content}</p>
        ) : (
          <div className="bubble-text markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPanel({ messages, pending, onSend, disabled, pendingConfirm, onResolveConfirm }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pending?.text, pending?.activities?.length, pendingConfirm]);

  const isEmpty = messages.length === 0 && !pending;

  return (
    <section className="chat-panel">
      <div className="chat-scroll" ref={scrollRef}>
        {isEmpty && (
          <div className="chat-empty">
            <PlaneIcon className="chat-empty-icon" />
            <h1>Where to, next?</h1>
            <p>
              Tell me your destination, dates, budget and what you like — I'll research flights, hotels,
              weather and places, then build a day-by-day plan with you.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <Bubble key={i} role={m.role} content={m.content} activities={m.activities} />
        ))}

        {pending && (
          <div className="bubble-row assistant">
            <div className="bubble pending">
              {pending.activities.length > 0 && <ActivityFeed items={pending.activities} />}
              {pending.text && (
                <div className="bubble-text markdown" style={{ marginTop: pending.activities.length ? 10 : 0 }}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{pending.text}</ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )}

        {pendingConfirm && (
          <div className="bubble-row assistant">
            <div className="confirm-banner">
              <p>
                This sounds like a different trip{pendingConfirm.currentDestination ? ` from your current one to ${pendingConfirm.currentDestination}` : ""}.
                Start a new chat for it?
              </p>
              <div className="confirm-banner-actions">
                <button className="confirm-banner-yes" onClick={() => onResolveConfirm(true)}>
                  Yes, new trip
                </button>
                <button className="confirm-banner-no" onClick={() => onResolveConfirm(false)}>
                  No, continue here
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <Composer
        onSend={onSend}
        disabled={disabled || !!pendingConfirm}
        placeholderWhenDisabled={pendingConfirm ? "Please confirm above first…" : "Wayfarer is working on it…"}
      />
    </section>
  );
}
