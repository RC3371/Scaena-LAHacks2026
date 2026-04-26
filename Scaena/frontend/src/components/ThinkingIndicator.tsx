import { motion } from "framer-motion";

export function ThinkingIndicator({ steps }: { steps: Array<{ step: string; conclusion?: string }> }) {
  if (!steps.length) return <p className="text-sm text-slate-400">Waiting for new conversation data...</p>;
  return (
    <motion.div
      className="space-y-2"
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.3 } } }}
    >
      {steps.slice(0, 12).map((item, idx) => (
        <motion.div
          key={`${item.step}-${idx}`}
          variants={{ hidden: { opacity: 0, x: -20 }, visible: { opacity: 1, x: 0 } }}
          className="rounded bg-slate-800 p-2 text-sm text-slate-200"
        >
          <div>🔍 {item.step}</div>
          {item.conclusion ? <div className="text-xs text-slate-400">→ {item.conclusion}</div> : null}
        </motion.div>
      ))}
    </motion.div>
  );
}
