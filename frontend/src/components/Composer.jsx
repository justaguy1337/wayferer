import { useRef, useState } from "react";
import { SendIcon } from "./icons";
import "./Composer.css";

export default function Composer({ onSend, disabled, placeholderWhenDisabled = "Wayfarer is working on it…" }) {
  const [value, setValue] = useState("");
  const taRef = useRef(null);

  const submit = () => {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
    if (taRef.current) taRef.current.style.height = "auto";
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const autoGrow = (e) => {
    setValue(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + "px";
  };

  return (
    <div className="composer">
      <textarea
        ref={taRef}
        value={value}
        onChange={autoGrow}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? placeholderWhenDisabled : "Plan a 7-day Japan trip from Bengaluru in November…"}
        rows={1}
        disabled={disabled}
      />
      <button className="composer-send" onClick={submit} disabled={disabled || !value.trim()} title="Send">
        <SendIcon width={17} height={17} />
      </button>
    </div>
  );
}
