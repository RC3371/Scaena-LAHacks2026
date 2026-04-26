import { useEffect, useRef, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

type CollapsibleTextProps = {
  text: string;
  collapsedLines?: number;
  defaultExpanded?: boolean;
  textClassName?: string;
  buttonClassName?: string;
};

export function CollapsibleText({
  text,
  collapsedLines = 2,
  defaultExpanded = false,
  textClassName = "",
  buttonClassName = "",
}: CollapsibleTextProps) {
  const textRef = useRef<HTMLParagraphElement>(null);
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [canCollapse, setCanCollapse] = useState(false);
  const [lineHeightPx, setLineHeightPx] = useState(24);

  useEffect(() => {
    setExpanded(defaultExpanded);
  }, [defaultExpanded, text]);

  useEffect(() => {
    const element = textRef.current;
    if (!element) return;

    const measure = () => {
      const styles = window.getComputedStyle(element);
      const parsedLineHeight = Number.parseFloat(styles.lineHeight);
      const parsedFontSize = Number.parseFloat(styles.fontSize);
      const nextLineHeight = Number.isFinite(parsedLineHeight)
        ? parsedLineHeight
        : (Number.isFinite(parsedFontSize) ? parsedFontSize * 1.4 : 24);

      setLineHeightPx(nextLineHeight);
      setCanCollapse(element.scrollHeight > nextLineHeight * collapsedLines + 2);
    };

    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [collapsedLines, text]);

  const Icon = expanded ? ChevronUp : ChevronDown;
  const collapsedStyle = !expanded && canCollapse
    ? { maxHeight: `${lineHeightPx * collapsedLines}px` }
    : undefined;

  return (
    <div>
      <p
        ref={textRef}
        style={collapsedStyle}
        className={`${textClassName} ${!expanded && canCollapse ? "overflow-hidden" : ""}`}
      >
        {text}
      </p>
      {canCollapse && (
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className={`mt-3 inline-flex items-center gap-1.5 rounded-full border-2 border-black px-3 py-1 text-[11px] font-bold uppercase font-[var(--font-space)] transition-all hover:-translate-y-0.5 ${buttonClassName}`}
        >
          <Icon size={13} strokeWidth={3} />
          {expanded ? "Minimize" : "Expand"}
        </button>
      )}
    </div>
  );
}
