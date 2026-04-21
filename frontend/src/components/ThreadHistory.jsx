export default function ThreadHistory({ messages }) {
  if (!messages || messages.length === 0) return null;

  return (
    <div
      className="space-y-2 p-4 bg-[#0f0f12] border border-white/5"
      data-testid="thread-history"
    >
      <div className="text-[10px] tracking-[0.15em] uppercase font-bold text-zinc-600 mb-3">
        Previous Messages
      </div>
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`flex gap-3 text-xs leading-relaxed ${
            msg.role === "account" ? "pl-6" : ""
          }`}
          data-testid={`thread-msg-${i}`}
        >
          <span
            className={`flex-shrink-0 text-[10px] tracking-wider uppercase font-bold w-20 text-right ${
              msg.role === "account" ? "text-white/60" : "text-zinc-500"
            }`}
          >
            {msg.role === "account" ? "You" : "User"}
          </span>
          <span
            className={`${
              msg.role === "account" ? "text-zinc-300" : "text-zinc-400"
            }`}
          >
            {msg.text}
          </span>
        </div>
      ))}
    </div>
  );
}
