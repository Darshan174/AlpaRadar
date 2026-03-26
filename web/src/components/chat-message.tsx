interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

export function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-[26px] px-4 py-4 text-sm leading-7 shadow-[0_18px_40px_rgba(2,6,23,0.16)] ${
          isUser
            ? "rounded-br-md bg-linear-to-br from-orange-500 to-amber-500 text-white"
            : "surface-panel rounded-bl-md text-(--color-text-primary)"
        }`}
      >
        <div className={`mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.22em] ${isUser ? "text-white/70" : "text-(--color-text-muted)"}`}>
          {isUser ? "You" : "AlphaRadar"}
        </div>
        <div className="whitespace-pre-wrap">{content}</div>
      </div>
    </div>
  );
}
