import { useEffect, useRef, useState } from "react";
import type { AgentEvent } from "../types";

export function useWebSocket(url?: string) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const target = url || `${(import.meta.env.VITE_API_URL || "http://localhost:8000").replace("http", "ws")}/ws/events`;
    const ws = new WebSocket(target);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (message) => {
      try {
        const parsed = JSON.parse(message.data) as AgentEvent;
        setEvents((prev) => [parsed, ...prev].slice(0, 300));
      } catch {
        // ignore malformed payload
      }
    };

    const keepAlive = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 20000);

    return () => {
      clearInterval(keepAlive);
      ws.close();
    };
  }, [url]);

  return { events, connected };
}
