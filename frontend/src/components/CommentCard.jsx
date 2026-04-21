import { useState } from "react";
import { FaYoutube, FaInstagram, FaFacebook, FaTiktok } from "react-icons/fa";
import { Check, RefreshCw, Pencil, X, ChevronDown, ChevronUp, Loader2, Save, ThumbsUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ThreadHistory from "@/components/ThreadHistory";

const PLATFORM_ICONS = {
  youtube: { icon: FaYoutube, color: "#FF0000", glow: "rgba(255,0,0,0.06)" },
  instagram: { icon: FaInstagram, color: "#E4405F", glow: "rgba(228,64,95,0.06)" },
  facebook: { icon: FaFacebook, color: "#1877F2", glow: "rgba(24,119,242,0.06)" },
  tiktok: { icon: FaTiktok, color: "#00F2EA", glow: "rgba(0,242,234,0.06)" },
};

export default function CommentCard({ comment, onApprove, onRegenerate, onEdit, onSkip, onToggleLike }) {
  const [editing, setEditing] = useState(false);
  const [editDraft, setEditDraft] = useState(comment.ai_draft);
  const [regenerating, setRegenrating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [showThread, setShowThread] = useState(false);

  const platform = PLATFORM_ICONS[comment.platform] || {};
  const PlatformIcon = platform.icon;
  const brandColor = platform.color || "#a1a1aa";
  const glowColor = platform.glow || "transparent";

  const handleRegenerate = async () => {
    setRegenrating(true);
    await onRegenerate(comment.id);
    setRegenrating(false);
  };

  const handleApprove = async () => {
    setApproving(true);
    await onApprove(comment.id);
    setApproving(false);
  };

  const handleSaveEdit = async () => {
    await onEdit(comment.id, editDraft);
    setEditing(false);
  };

  const handleCancelEdit = () => {
    setEditDraft(comment.ai_draft);
    setEditing(false);
  };

  return (
    <article
      className="flex flex-col gap-5 p-6 rounded-xl border border-white/[0.06] hover:border-white/[0.12] transition-all duration-300 shadow-lg shadow-black/20 relative overflow-hidden"
      style={{
        background: `linear-gradient(135deg, ${glowColor} 0%, #16161e 40%, #16161e 100%)`,
        borderLeft: `3px solid ${brandColor}`,
      }}
      data-testid={`comment-card-${comment.id}`}
    >
      {/* Header row: platform badge + commenter info */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          {/* Platform icon */}
          {PlatformIcon && (
            <div
              className="w-9 h-9 flex items-center justify-center flex-shrink-0 rounded-lg"
              style={{ backgroundColor: `${brandColor}15`, border: `1px solid ${brandColor}30` }}
              data-testid={`platform-icon-${comment.platform}`}
            >
              <PlatformIcon className="w-4 h-4" style={{ color: brandColor }} />
            </div>
          )}
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-zinc-200" data-testid="commenter-name">
                {comment.commenter_name}
              </span>
              <span className="text-[10px] tracking-[0.15em] uppercase font-bold text-zinc-600">
                {comment.account_username}
              </span>
              {comment.is_thread_reply && (
                <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest border border-white/[0.06] text-zinc-500 rounded-md">
                  Thread Reply
                </span>
              )}
              {comment.auto_liked ? (
                <button
                  onClick={() => onToggleLike(comment.id)}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md hover:bg-emerald-500/20 transition-colors cursor-pointer"
                  data-testid="auto-liked-badge"
                  title="Click to unlike"
                >
                  <ThumbsUp className="w-2.5 h-2.5" />
                  Liked
                </button>
              ) : (
                <button
                  onClick={() => onToggleLike(comment.id)}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-zinc-500/10 text-zinc-500 border border-zinc-500/20 rounded-md hover:bg-zinc-500/20 transition-colors cursor-pointer"
                  data-testid="not-liked-badge"
                  title="Click to like"
                >
                  <ThumbsUp className="w-2.5 h-2.5" />
                  Not Liked
                </button>
              )}
            </div>
            {comment.post_title && (
              <p className="text-xs text-zinc-600 mt-0.5 truncate" data-testid="post-title">
                on: {comment.post_title}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Thread history toggle */}
      {comment.thread_history && comment.thread_history.length > 0 && (
        <div>
          <button
            onClick={() => setShowThread(!showThread)}
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            data-testid="toggle-thread-btn"
          >
            {showThread ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {showThread ? "Hide thread" : `Show thread (${comment.thread_history.length} messages)`}
          </button>
          {showThread && (
            <div className="mt-3">
              <ThreadHistory messages={comment.thread_history} />
            </div>
          )}
        </div>
      )}

      {/* Original comment */}
      <div className="pl-4 border-l-2 rounded-sm" style={{ borderColor: `${brandColor}60` }}>
        <p className="text-sm text-zinc-300 leading-relaxed" data-testid="comment-text">
          {comment.comment_text}
        </p>
      </div>

      {/* AI Draft reply */}
      <div className="relative" data-testid="ai-draft-section">
        <div className="text-[10px] tracking-[0.2em] uppercase font-bold text-zinc-600 mb-2">
          AI Draft Reply
        </div>
        {editing ? (
          <div className="space-y-2">
            <Textarea
              value={editDraft}
              onChange={(e) => setEditDraft(e.target.value)}
              className="bg-[#1c1c24] border-white/[0.08] text-sm text-zinc-200 min-h-[80px] rounded-lg focus:ring-1 focus:ring-zinc-400 focus:border-white/[0.12] resize-none"
              data-testid="edit-draft-textarea"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleSaveEdit}
                className="bg-zinc-100 text-zinc-900 hover:bg-white rounded-lg px-4 py-1.5 text-xs font-bold"
                data-testid="save-edit-btn"
              >
                <Save className="w-3 h-3 mr-1.5" />
                Save
              </Button>
              <Button
                onClick={handleCancelEdit}
                variant="ghost"
                className="text-zinc-500 hover:text-zinc-300 rounded-lg px-4 py-1.5 text-xs"
                data-testid="cancel-edit-btn"
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-[#1c1c24] rounded-lg border-l-2 text-sm text-zinc-300 leading-relaxed" style={{ borderColor: `${brandColor}80` }}>
            <p data-testid="ai-draft-text">{comment.ai_draft}</p>
          </div>
        )}
      </div>

      {/* Action buttons */}
      {!editing && (
        <div className="flex items-center gap-2 pt-1" data-testid="action-buttons">
          <Button
            onClick={handleApprove}
            disabled={approving}
            className="bg-zinc-100 text-zinc-900 hover:bg-white rounded-lg px-5 py-2 text-xs font-bold transition-all duration-200 shadow-sm shadow-white/10"
            data-testid="approve-comment-btn"
          >
            {approving ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
            ) : (
              <Check className="w-3.5 h-3.5 mr-1.5" />
            )}
            Approve
          </Button>
          <Button
            onClick={() => setEditing(true)}
            variant="outline"
            className="border border-white/[0.08] bg-transparent text-zinc-300 hover:bg-white/[0.05] hover:text-zinc-100 rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-200"
            data-testid="edit-comment-btn"
          >
            <Pencil className="w-3.5 h-3.5 mr-1.5" />
            Edit
          </Button>
          <Button
            onClick={handleRegenerate}
            disabled={regenerating}
            variant="ghost"
            className="text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.04] rounded-lg px-4 py-2 text-xs transition-all duration-200"
            data-testid="regenerate-comment-btn"
          >
            {regenerating ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            )}
            Regenerate
          </Button>
          <Button
            onClick={() => onSkip(comment.id)}
            variant="ghost"
            className="text-zinc-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-200 ml-auto"
            data-testid="skip-comment-btn"
          >
            <X className="w-3.5 h-3.5 mr-1.5" />
            Skip
          </Button>
        </div>
      )}
    </article>
  );
}
