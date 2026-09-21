import { useState } from "react";
import { PlaneIcon, PlusIcon, TrashIcon, PencilIcon } from "./icons";
import "./Sidebar.css";

function relativeTime(ts) {
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export default function Sidebar({ sessions, activeId, onSelect, onCreate, onRename, onDelete }) {
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const startEdit = (s) => {
    setEditingId(s.id);
    setEditValue(s.title);
  };

  const commitEdit = () => {
    if (editValue.trim()) onRename(editingId, editValue.trim());
    setEditingId(null);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <PlaneIcon className="brand-icon" />
        <span>Wayfarer</span>
      </div>

      <button className="new-trip-btn" onClick={onCreate}>
        <PlusIcon width={16} height={16} />
        New trip
      </button>

      <div className="trip-list">
        {sessions.length === 0 && <p className="trip-list-empty">No trips yet — start one above.</p>}
        {sessions.map((s) => (
          <div key={s.id} className={`trip-stub ${s.id === activeId ? "active" : ""}`} onClick={() => onSelect(s.id)}>
            <div className="trip-stub-notch" />
            {editingId === s.id ? (
              <input
                autoFocus
                className="trip-rename-input"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onBlur={commitEdit}
                onKeyDown={(e) => e.key === "Enter" && commitEdit()}
                onClick={(e) => e.stopPropagation()}
              />
            ) : confirmDeleteId === s.id ? (
              <div className="trip-stub-confirm" onClick={(e) => e.stopPropagation()}>
                <span>Delete this trip?</span>
                <button
                  className="confirm-yes"
                  onClick={() => {
                    onDelete(s.id);
                    setConfirmDeleteId(null);
                  }}
                >
                  Yes
                </button>
                <button className="confirm-no" onClick={() => setConfirmDeleteId(null)}>
                  No
                </button>
              </div>
            ) : (
              <div className="trip-stub-body">
                <span className="trip-title">{s.title}</span>
                <span className="trip-time">{relativeTime(s.updated_at)}</span>
              </div>
            )}
            {confirmDeleteId !== s.id && (
              <div className="trip-stub-actions">
                <button
                  title="Rename"
                  onClick={(e) => {
                    e.stopPropagation();
                    startEdit(s);
                  }}
                >
                  <PencilIcon width={13} height={13} />
                </button>
                <button
                  title="Delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    setConfirmDeleteId(s.id);
                  }}
                >
                  <TrashIcon width={13} height={13} />
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="sidebar-footer">Single-trip planning, saved locally in SQLite.</div>
    </aside>
  );
}
