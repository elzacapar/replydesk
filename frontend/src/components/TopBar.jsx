import { RefreshCw, CheckCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function TopBar({
  stats,
  onFetchNew,
  onApproveAll,
  fetching,
  approvingAll,
  commentCount,
}) {
  return (
    <header
      className="sticky top-0 z-50 backdrop-blur-xl bg-[#13131a]/80 border-b border-white/[0.06] px-8 h-[72px] flex items-center justify-between"
      data-testid="topbar"
    >
      {/* Stats */}
      <div className="flex items-center gap-6">
        <div className="flex flex-col" data-testid="stat-pending">
          <span className="text-[10px] tracking-[0.2em] uppercase font-bold text-zinc-600">
            Pending
          </span>
          <span className="text-2xl font-bold tracking-tight text-amber-400" style={{ fontFamily: "'Cabinet Grotesk', 'Manrope', sans-serif" }}>
            {stats.total_pending}
          </span>
        </div>
        <div className="w-px h-10 bg-white/[0.06]" />
        <div className="flex flex-col" data-testid="stat-approved">
          <span className="text-[10px] tracking-[0.2em] uppercase font-bold text-zinc-600">
            Approved Today
          </span>
          <span className="text-2xl font-bold tracking-tight text-emerald-400" style={{ fontFamily: "'Cabinet Grotesk', 'Manrope', sans-serif" }}>
            {stats.total_approved_today}
          </span>
        </div>
        <div className="w-px h-10 bg-white/[0.06]" />
        <div className="flex flex-col" data-testid="stat-accounts">
          <span className="text-[10px] tracking-[0.2em] uppercase font-bold text-zinc-600">
            Accounts
          </span>
          <span className="text-2xl font-bold tracking-tight text-sky-400" style={{ fontFamily: "'Cabinet Grotesk', 'Manrope', sans-serif" }}>
            {stats.total_accounts}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button
          onClick={onFetchNew}
          disabled={fetching}
          className="bg-transparent border border-white/[0.08] text-zinc-300 hover:bg-white/[0.05] hover:text-zinc-100 rounded-lg px-5 py-2 text-sm font-semibold transition-all duration-200"
          data-testid="fetch-new-btn"
        >
          {fetching ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <RefreshCw className="w-4 h-4 mr-2" />
          )}
          Fetch New
        </Button>
        <Button
          onClick={onApproveAll}
          disabled={approvingAll || commentCount === 0}
          className="bg-zinc-100 text-zinc-900 hover:bg-white rounded-lg px-5 py-2 text-sm font-bold transition-all duration-200 shadow-sm shadow-white/10"
          data-testid="approve-all-btn"
        >
          {approvingAll ? (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          ) : (
            <CheckCheck className="w-4 h-4 mr-2" />
          )}
          Approve All
        </Button>
      </div>
    </header>
  );
}
