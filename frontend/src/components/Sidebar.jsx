import { useState } from "react";
import { FaYoutube, FaInstagram, FaFacebook, FaTiktok } from "react-icons/fa";
import { ChevronDown, Plus, Trash2, LayoutDashboard, Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const PLATFORM_CONFIG = {
  youtube: { icon: FaYoutube, color: "#ff0000", label: "YouTube" },
  instagram: { icon: FaInstagram, color: "#e1306c", label: "Instagram" },
  facebook: { icon: FaFacebook, color: "#1877f2", label: "Facebook" },
  tiktok: { icon: FaTiktok, color: "#00f2fe", label: "TikTok" },
};

export default function Sidebar({
  platforms,
  selectedAccountId,
  selectedPlatform,
  onSelectAccount,
  onSelectPlatform,
  onShowAll,
  onConnectAccount,
  onDeleteAccount,
  loading,
}) {
  const [openPlatforms, setOpenPlatforms] = useState({
    youtube: true,
    instagram: true,
    facebook: true,
    tiktok: true,
  });

  const togglePlatform = (platform) => {
    setOpenPlatforms((prev) => ({ ...prev, [platform]: !prev[platform] }));
  };

  return (
    <TooltipProvider>
      <aside
        className="w-64 fixed left-0 top-0 h-screen border-r border-white/10 bg-[#09090b] flex flex-col z-40"
        data-testid="sidebar"
      >
        {/* Logo */}
        <div className="px-6 py-5 border-b border-white/10">
          <h1
            className="text-lg font-bold tracking-tight text-white"
            style={{ fontFamily: "'Cabinet Grotesk', 'Manrope', sans-serif" }}
            data-testid="app-title"
          >
            Reply Manager
          </h1>
          <p className="text-[10px] tracking-[0.2em] uppercase font-bold text-zinc-500 mt-1">
            Social Comments
          </p>
        </div>

        {/* All Comments button */}
        <div className="px-4 pt-4 pb-2">
          <button
            onClick={onShowAll}
            className={`w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
              !selectedAccountId && !selectedPlatform
                ? "bg-white/10 text-white"
                : "text-zinc-400 hover:text-white hover:bg-white/5"
            }`}
            data-testid="show-all-btn"
          >
            <LayoutDashboard className="w-4 h-4" />
            All Comments
          </button>
        </div>

        {/* Platform list */}
        <ScrollArea className="flex-1 px-4 pb-4">
          {loading ? (
            <div className="flex items-center justify-center py-8" data-testid="sidebar-loading">
              <Loader2 className="w-5 h-5 text-zinc-500 animate-spin" />
            </div>
          ) : (
            <div className="space-y-1 mt-2">
              {platforms.map((platform) => {
                const config = PLATFORM_CONFIG[platform.platform];
                if (!config) return null;
                const Icon = config.icon;
                const isSelectedPlatform =
                  selectedPlatform === platform.platform && !selectedAccountId;

                return (
                  <Collapsible
                    key={platform.platform}
                    open={openPlatforms[platform.platform]}
                    onOpenChange={() => togglePlatform(platform.platform)}
                  >
                    <div className="flex items-center">
                      <CollapsibleTrigger asChild>
                        <button
                          className={`flex-1 flex items-center gap-3 px-3 py-2.5 text-sm font-semibold transition-all duration-200 ${
                            isSelectedPlatform
                              ? "bg-white/10 text-white"
                              : "text-zinc-300 hover:text-white hover:bg-white/5"
                          }`}
                          onClick={(e) => {
                            e.preventDefault();
                            onSelectPlatform(platform.platform);
                            if (!openPlatforms[platform.platform]) {
                              togglePlatform(platform.platform);
                            }
                          }}
                          data-testid={`platform-btn-${platform.platform}`}
                        >
                          <Icon
                            className="w-4 h-4 flex-shrink-0"
                            style={{ color: config.color }}
                          />
                          <span className="flex-1 text-left">{config.label}</span>
                          <span className="text-[10px] text-zinc-500 font-bold mr-1">
                            {platform.accounts.length}
                          </span>
                          <ChevronDown
                            className={`w-3.5 h-3.5 text-zinc-500 transition-transform duration-200 ${
                              openPlatforms[platform.platform] ? "rotate-180" : ""
                            }`}
                          />
                        </button>
                      </CollapsibleTrigger>
                    </div>
                    <CollapsibleContent>
                      <div className="ml-4 mt-1 space-y-0.5 border-l border-white/5 pl-3">
                        {platform.accounts.map((account) => (
                          <div
                            key={account.id}
                            className={`group flex items-center gap-2 px-2 py-1.5 text-sm transition-all duration-200 cursor-pointer ${
                              selectedAccountId === account.id
                                ? "bg-white/10 text-white"
                                : "text-zinc-400 hover:text-white hover:bg-white/5"
                            }`}
                            onClick={() =>
                              onSelectAccount(account.id, platform.platform)
                            }
                            data-testid={`account-item-${account.id}`}
                          >
                            <div
                              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                              style={{
                                backgroundColor: account.is_connected
                                  ? "#22c55e"
                                  : "#71717a",
                              }}
                            />
                            <span className="flex-1 truncate text-xs font-medium">
                              {account.username}
                            </span>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteAccount(account.id);
                                  }}
                                  className="opacity-0 group-hover:opacity-100 transition-opacity text-zinc-500 hover:text-red-500"
                                  data-testid={`delete-account-${account.id}`}
                                >
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              </TooltipTrigger>
                              <TooltipContent>Remove account</TooltipContent>
                            </Tooltip>
                          </div>
                        ))}
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={() =>
                                onConnectAccount(platform.platform)
                              }
                              className="w-full flex items-center gap-2 px-2 py-1.5 text-xs text-zinc-500 hover:text-white transition-all duration-200 hover:bg-white/5"
                              data-testid={`add-account-${platform.platform}`}
                            >
                              <Plus className="w-3 h-3" />
                              <span>Add Account</span>
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>
                            {platform.configured
                              ? `Connect ${config.label} account`
                              : `Configure ${config.label} credentials first`}
                          </TooltipContent>
                        </Tooltip>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                );
              })}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10">
          <p className="text-[10px] tracking-[0.15em] uppercase text-zinc-600 font-bold">
            Comment Reply Manager
          </p>
        </div>
      </aside>
    </TooltipProvider>
  );
}
