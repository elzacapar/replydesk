import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import CommentQueue from "@/components/CommentQueue";
import EmptyState from "@/components/EmptyState";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [platforms, setPlatforms] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [comments, setComments] = useState([]);
  const [stats, setStats] = useState({ total_pending: 0, total_approved_today: 0, total_accounts: 0, total_skipped: 0 });
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [approvingAll, setApprovingAll] = useState(false);

  const fetchPlatforms = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/platforms`);
      setPlatforms(res.data);
    } catch (e) {
      console.error("Failed to fetch platforms:", e);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/stats`);
      setStats(res.data);
    } catch (e) {
      console.error("Failed to fetch stats:", e);
    }
  }, []);

  const fetchComments = useCallback(async () => {
    try {
      const params = { status: "pending" };
      if (selectedAccountId) params.account_id = selectedAccountId;
      else if (selectedPlatform) params.platform = selectedPlatform;
      const res = await axios.get(`${API}/comments`, { params });
      setComments(res.data);
    } catch (e) {
      console.error("Failed to fetch comments:", e);
    }
  }, [selectedAccountId, selectedPlatform]);

  const initApp = useCallback(async () => {
    setLoading(true);
    // Seed demo data on first load
    try {
      await axios.post(`${API}/seed-demo`);
    } catch (e) { /* ignore */ }
    await Promise.all([fetchPlatforms(), fetchStats(), fetchComments()]);
    setLoading(false);
  }, [fetchPlatforms, fetchStats, fetchComments]);

  useEffect(() => {
    initApp();
  }, [initApp]);

  useEffect(() => {
    fetchComments();
  }, [selectedAccountId, selectedPlatform, fetchComments]);

  const handleFetchNew = async () => {
    setFetching(true);
    try {
      const res = await axios.post(`${API}/comments/fetch`);
      toast.success(`Fetched ${res.data.total_new} new comments`);
      if (res.data.errors?.length > 0) {
        toast.error(`Errors: ${res.data.errors.join(", ")}`);
      }
      await Promise.all([fetchComments(), fetchStats(), fetchPlatforms()]);
    } catch (e) {
      toast.error("Failed to fetch new comments");
    }
    setFetching(false);
  };

  const handleApproveAll = async () => {
    setApprovingAll(true);
    try {
      const params = {};
      if (selectedAccountId) params.account_id = selectedAccountId;
      const res = await axios.post(`${API}/comments/approve-all`, null, { params });
      toast.success(`Approved ${res.data.approved_count} comments`);
      await Promise.all([fetchComments(), fetchStats()]);
    } catch (e) {
      toast.error("Failed to approve all");
    }
    setApprovingAll(false);
  };

  const handleApprove = async (commentId) => {
    try {
      await axios.post(`${API}/comments/${commentId}/approve`);
      toast.success("Reply approved");
      setComments(prev => prev.filter(c => c.id !== commentId));
      fetchStats();
    } catch (e) {
      toast.error("Failed to approve");
    }
  };

  const handleRegenerate = async (commentId) => {
    try {
      const res = await axios.post(`${API}/comments/${commentId}/regenerate`);
      setComments(prev =>
        prev.map(c => c.id === commentId ? { ...c, ai_draft: res.data.new_draft } : c)
      );
      toast.success("Draft regenerated");
    } catch (e) {
      toast.error("Failed to regenerate");
    }
  };

  const handleEdit = async (commentId, newDraft) => {
    try {
      await axios.put(`${API}/comments/${commentId}/edit`, { draft: newDraft });
      setComments(prev =>
        prev.map(c => c.id === commentId ? { ...c, ai_draft: newDraft } : c)
      );
    } catch (e) {
      toast.error("Failed to save edit");
    }
  };

  const handleSkip = async (commentId) => {
    try {
      await axios.post(`${API}/comments/${commentId}/skip`);
      setComments(prev => prev.filter(c => c.id !== commentId));
      fetchStats();
      toast.success("Comment skipped");
    } catch (e) {
      toast.error("Failed to skip");
    }
  };

  const handleToggleLike = async (commentId) => {
    try {
      const res = await axios.post(`${API}/comments/${commentId}/toggle-like`);
      setComments(prev =>
        prev.map(c => c.id === commentId ? { ...c, auto_liked: res.data.auto_liked } : c)
      );
    } catch (e) {
      toast.error("Failed to toggle like");
    }
  };

  const handleSelectAccount = (accountId, platform) => {
    if (selectedAccountId === accountId) {
      setSelectedAccountId(null);
      setSelectedPlatform(null);
    } else {
      setSelectedAccountId(accountId);
      setSelectedPlatform(platform);
    }
  };

  const handleSelectPlatform = (platform) => {
    if (selectedPlatform === platform && !selectedAccountId) {
      setSelectedPlatform(null);
    } else {
      setSelectedAccountId(null);
      setSelectedPlatform(platform);
    }
  };

  const handleShowAll = () => {
    setSelectedAccountId(null);
    setSelectedPlatform(null);
  };

  const handleConnectAccount = async (platform) => {
    try {
      const res = await axios.get(`${API}/accounts/${platform}/auth-url`);
      window.open(res.data.auth_url, "_blank");
    } catch (e) {
      const msg = e.response?.data?.detail || "Failed to start OAuth flow";
      toast.error(msg);
    }
  };

  const handleDeleteAccount = async (accountId) => {
    try {
      await axios.delete(`${API}/accounts/${accountId}`);
      toast.success("Account removed");
      await Promise.all([fetchPlatforms(), fetchComments(), fetchStats()]);
      if (selectedAccountId === accountId) {
        setSelectedAccountId(null);
        setSelectedPlatform(null);
      }
    } catch (e) {
      toast.error("Failed to remove account");
    }
  };

  const handleUpdateTone = async (accountId, tone) => {
    try {
      await axios.put(`${API}/accounts/${accountId}/tone`, { tone_preset: tone });
      toast.success(`Tone set to ${tone}`);
      fetchPlatforms();
    } catch (e) {
      toast.error("Failed to update tone");
    }
  };

  const selectedAccount = platforms
    .flatMap(p => p.accounts)
    .find(a => a.id === selectedAccountId);

  const currentTitle = selectedAccount
    ? selectedAccount.username
    : selectedPlatform
      ? `All ${selectedPlatform.charAt(0).toUpperCase() + selectedPlatform.slice(1)} Comments`
      : "All Comments";

  return (
    <div className="flex min-h-screen bg-[#13131a]" data-testid="app-root">
      <Toaster
        theme="dark"
        position="top-right"
        toastOptions={{
          style: { background: "#1c1c24", border: "1px solid rgba(255,255,255,0.06)", color: "#d4d4dc" },
        }}
      />
      <Sidebar
        platforms={platforms}
        selectedAccountId={selectedAccountId}
        selectedPlatform={selectedPlatform}
        onSelectAccount={handleSelectAccount}
        onSelectPlatform={handleSelectPlatform}
        onShowAll={handleShowAll}
        onConnectAccount={handleConnectAccount}
        onDeleteAccount={handleDeleteAccount}
        onUpdateTone={handleUpdateTone}
        loading={loading}
      />
      <div className="flex-1 ml-64 flex flex-col min-h-screen">
        <TopBar
          stats={stats}
          onFetchNew={handleFetchNew}
          onApproveAll={handleApproveAll}
          fetching={fetching}
          approvingAll={approvingAll}
          commentCount={comments.length}
        />
        <main className="flex-1 p-8">
          <div className="max-w-4xl mx-auto">
            <div className="mb-6">
              <h2
                className="text-2xl tracking-tight font-bold text-zinc-100"
                style={{ fontFamily: "'Cabinet Grotesk', 'Manrope', sans-serif" }}
                data-testid="queue-title"
              >
                {currentTitle}
              </h2>
              <p className="text-sm text-zinc-500 mt-1" data-testid="queue-count">
                {comments.length} pending {comments.length === 1 ? "comment" : "comments"}
              </p>
            </div>
            {loading ? (
              <div className="flex items-center justify-center py-20" data-testid="loading-state">
                <div className="w-6 h-6 border-2 border-zinc-600 border-t-zinc-300 rounded-full animate-spin-slow" />
              </div>
            ) : comments.length === 0 ? (
              <EmptyState selectedPlatform={selectedPlatform} />
            ) : (
              <CommentQueue
                comments={comments}
                onApprove={handleApprove}
                onRegenerate={handleRegenerate}
                onEdit={handleEdit}
                onSkip={handleSkip}
                onToggleLike={handleToggleLike}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
