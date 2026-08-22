import { useEffect } from "react";

export default function Toast({ message, variant = "success", onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3200);
    return () => clearTimeout(t);
  }, [onClose]);

  if (!message) return null;

  return (
    <div className={`toast ${variant === "error" ? "error" : ""}`} role="status">
      {message}
    </div>
  );
}
