import { motion } from "framer-motion";
import type { AgentStatus } from "../types";

interface AgentNodeProps {
  name: string;
  status: AgentStatus;
  message?: string;
  onClick?: () => void;
}

const statusClass: Record<AgentStatus, string> = {
  idle: "border-slate-600 bg-slate-900",
  working: "border-blue-500 bg-blue-950",
  complete: "border-emerald-500 bg-emerald-950",
  error: "border-red-500 bg-red-950",
};

export function AgentNode({ name, status, message, onClick }: AgentNodeProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      onClick={onClick}
      className={`w-full rounded-xl border p-4 text-left ${statusClass[status]}`}
    >
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-semibold text-white">{name}</h3>
        <span className="text-xs uppercase text-slate-300">{status}</span>
      </div>
      <p className="line-clamp-2 text-sm text-slate-200">{message || "Waiting for activity..."}</p>
    </motion.button>
  );
}
