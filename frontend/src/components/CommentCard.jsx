import { useState } from "react";
import { FaYoutube, FaInstagram, FaFacebook, FaTiktok } from "react-icons/fa";
import { Check, RefreshCw, Pencil, X, ChevronDown, ChevronUp, Loader2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import ThreadHistory from "@/components/ThreadHistory";

const PLATFORM_ICONS = {
  youtube: { icon: FaYoutube, color: "#ff0000" },
  instagram: { icon: FaInstagram, color: "#e1306c" },
  facebook: { icon: FaFacebook, color: "#1877f2" },
  tiktok: { icon: FaTiktok, color: "#00f2fe" },
};

export default function CommentCard({ comment, onApprove, onRegenerate, onEdit, onSkip }) {
  const [editing, setEditing] = useState(false);
  const [editDraft, setEditDraft] = useState(comment.ai_draft);
  const [regenerating, setRegenrating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [showThread, setShowThread] = useState(false);

  const platform = PLATFORM_ICONS[comment.platform] || {};
  const PlatformIcon = platform.icon;

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
      className="flex flex-col gap-5 p-6 bg-[#09090b] border border-white/10 hover:border-white/20 transition-all duration-200"
      data-testid={`comment-card-${comment.id}`}
    >
      {/* Header row: platform badge + commenter info */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 min-w-0">
          {/* Platform icon */}
          {PlatformIcon && (
            <div
              className="w-9 h-9 flex items-center justify-center flex-shrink-0 border border-white/10"
              data-testid={`platform-icon-${comment.platform}`}
            >
              <PlatformIcon className="w-4 h-4" style={{ color: platform.color }} />
            </div>
          )}
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-bold text-white" data-testid="commenter-name">
                {comment.commenter_name}
              </span>
              <span className="text-[10px] tracking-[0.15em] uppercase font-bold text-zinc-500">
                {comment.account_username}
              </span>
              {comment.is_thread_reply && (
                <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-widest border border-white/10 text-zinc-400">
                  Thread Reply
                </span>
              )}
            </div>
            {comment.post_title && (
              <p className="text-xs text-zinc-500 mt-0.5 truncate" data-testid="post-title">
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
            className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-white transition-colors"
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
      <div className="pl-4 border-l-2 border-zinc-700">
        <p className="text-sm text-zinc-200 leading-relaxed" data-testid="comment-text">
          {comment.comment_text}
        </p>
      </div>

      {/* AI Draft reply */}
      <div className="relative" data-testid="ai-draft-section">
        <div className="text-[10px] tracking-[0.2em] uppercase font-bold text-zinc-500 mb-2">
          AI Draft Reply
        </div>
        {editing ? (
          <div className="space-y-2">
            <Textarea
              value={editDraft}
              onChange={(e) => setEditDraft(e.target.value)}
              className="bg-[#18181b] border-white/10 text-sm text-white min-h-[80px] rounded-none focus:ring-1 focus:ring-white focus:border-white/20 resize-none"
              data-testid="edit-draft-textarea"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleSaveEdit}
                className="bg-white text-[#09090b] hover:bg-zinc-200 rounded-none px-4 py-1.5 text-xs font-bold"
                data-testid="save-edit-btn"
              >
                <Save className="w-3 h-3 mr-1.5" />
                Save
              </Button>
              <Button
                onClick={handleCancelEdit}
                variant="ghost"
                className="text-zinc-400 hover:text-white rounded-none px-4 py-1.5 text-xs"
                data-testid="cancel-edit-btn"
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-[#18181b] border-l-2 border-white text-sm text-zinc-200 leading-relaxed">
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
            className="bg-white text-[#09090b] hover:bg-zinc-200 rounded-none px-5 py-2 text-xs font-bold transition-all duration-200"
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
            className="border border-white/10 bg-transparent text-white hover:bg-white/5 hover:text-white rounded-none px-4 py-2 text-xs font-semibold transition-all duration-200"
            data-testid="edit-comment-btn"
          >
            <Pencil className="w-3.5 h-3.5 mr-1.5" />
            Edit
          </Button>
          <Button
            onClick={handleRegenerate}
            disabled={regenerating}
            variant="ghost"
            className="text-zinc-400 hover:text-white hover:bg-white/5 rounded-none px-4 py-2 text-xs transition-all duration-200"
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
            className="text-zinc-500 hover:text-red-500 hover:bg-red-500/10 rounded-none px-4 py-2 text-xs font-semibold transition-all duration-200 ml-auto"
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
