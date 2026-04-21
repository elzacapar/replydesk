import { MessageSquare, CheckCircle } from "lucide-react";

export default function EmptyState({ selectedPlatform }) {
  return (
    <div
      className="flex flex-col items-center justify-center py-20 text-center"
      data-testid="empty-state"
    >
      <div className="w-16 h-16 flex items-center justify-center border border-white/[0.06] mb-6">
        <CheckCircle className="w-8 h-8 text-zinc-700" />
      </div>
      <h3
        className="text-xl font-bold text-zinc-200 tracking-tight mb-2"
        style={{ fontFamily: "'Cabinet Grotesk', 'Manrope', sans-serif" }}
      >
        All caught up
      </h3>
      <p className="text-sm text-zinc-600 max-w-sm leading-relaxed">
        {selectedPlatform
          ? `No pending comments for ${selectedPlatform}. Click "Fetch New" to check for new comments.`
          : 'No pending comments across all accounts. Click "Fetch New" to pull in the latest comments.'}
      </p>
      <div className="mt-8 flex items-center gap-2 text-xs text-zinc-700">
        <MessageSquare className="w-3.5 h-3.5" />
        <span>Comments will appear here when fetched</span>
      </div>
    </div>
  );
}
