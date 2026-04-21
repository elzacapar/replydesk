import CommentCard from "@/components/CommentCard";

export default function CommentQueue({ comments, onApprove, onRegenerate, onEdit, onSkip, onToggleLike }) {
  return (
    <div className="space-y-4" data-testid="comment-queue">
      {comments.map((comment, index) => (
        <div
          key={comment.id}
          className="animate-fade-slide-up"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <CommentCard
            comment={comment}
            onApprove={onApprove}
            onRegenerate={onRegenerate}
            onEdit={onEdit}
            onSkip={onSkip}
            onToggleLike={onToggleLike}
          />
        </div>
      ))}
    </div>
  );
}
