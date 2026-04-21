import { useState } from "react";
import { FaYoutube, FaInstagram, FaFacebook, FaTiktok } from "react-icons/fa";
import { ChevronDown, Plus, Trash2, LayoutDashboard, Loader2 } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const PLATFORM_CONFIG = {
  youtube: { icon: FaYoutube, color: "#cc3333", label: "YouTube" },
  instagram: { icon: FaInstagram, color: "#b84d70", label: "Instagram" },
  facebook: { icon: FaFacebook, color: "#5090d4", label: "Facebook" },
  tiktok: { icon: FaTiktok, color: "#4db8c7", label: "TikTok" },
};

const TONE_OPTIONS = [
  { value: "casual", label: "Casual" },
  { value: "professional", label: "Professional" },
  { value: "witty", label: "Witty" },
  { value: "warm", label: "Warm" },
];

export default function Sidebar({
  platforms,
  selectedAccountId,
  selectedPlatform,
  onSelectAccount,
  onSelectPlatform,
  onShowAll,
  onConnectAccount,
  onDeleteAccount,
  onUpdateTone,
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
        className="w-64 fixed left-0 top-0 h-screen border-r border-white/[0.06] bg-[#13131a] flex flex-col z-40"
        data-testid="sidebar"
      >
        {/* Logo */}
        <div className="px-6 py-5 border-b border-white/[0.06]">
          <h1
            className="text-lg font-bold tracking-tight text-zinc-100"
            style={{ fontFamily: "'Cabinet Grotesk', 'Manrope', sans-serif" }}
            data-testid="app-title"
          >
            Reply Manager
          </h1>
          <p className="text-[10px] tracking-[0.2em] uppercase font-bold text-zinc-600 mt-1">
            Social Comments
          </p>
        </div>

        {/* All Comments button */}
        <div className="px-4 pt-4 pb-2">
          <button
            onClick={onShowAll}
            className={`w-full flex items-center gap-3 px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
              !selectedAccountId && !selectedPlatform
                ? "bg-white/[0.07] text-zinc-100"
                : "text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.04]"
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
              <Loader2 className="w-5 h-5 text-zinc-600 animate-spin" />
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
                              ? "bg-white/[0.07] text-zinc-100"
                              : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
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
                          <span className="text-[10px] text-zinc-600 font-bold mr-1">
                            {platform.accounts.length}
                          </span>
                          <ChevronDown
                            className={`w-3.5 h-3.5 text-zinc-600 transition-transform duration-200 ${
                              openPlatforms[platform.platform] ? "rotate-180" : ""
                            }`}
                          />
                        </button>
                      </CollapsibleTrigger>
                    </div>
                    <CollapsibleContent>
                      <div className="ml-4 mt-1 space-y-0.5 border-l border-white/[0.04] pl-3">
                        {platform.accounts.map((account) => (
                          <div key={account.id}>
                            <div
                              className={`group flex items-center gap-2 px-2 py-1.5 text-sm transition-all duration-200 cursor-pointer ${
                                selectedAccountId === account.id
                                  ? "bg-white/[0.07] text-zinc-100"
                                  : "text-zinc-500 hover:text-zinc-200 hover:bg-white/[0.04]"
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
                                    ? "#4ade80"
                                    : "#52525b",
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
                                    className="opacity-0 group-hover:opacity-100 transition-opacity text-zinc-600 hover:text-red-400"
                                    data-testid={`delete-account-${account.id}`}
                                  >
                                    <Trash2 className="w-3 h-3" />
                                  </button>
                                </TooltipTrigger>
                                <TooltipContent>Remove account</TooltipContent>
                              </Tooltip>
                            </div>
                            {/* Tone Preset Dropdown */}
                            <div className="flex items-center gap-1.5 pl-6 py-1">
                              <span className="text-[9px] tracking-wider uppercase text-zinc-600 font-bold">
                                Tone:
                              </span>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <button
                                    className="text-[10px] font-semibold text-zinc-400 hover:text-zinc-200 transition-colors flex items-center gap-1 px-1.5 py-0.5 rounded-sm hover:bg-white/[0.04]"
                                    data-testid={`tone-selector-${account.id}`}
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {(account.tone_preset || "warm").charAt(0).toUpperCase() + (account.tone_preset || "warm").slice(1)}
                                    <ChevronDown className="w-2.5 h-2.5" />
                                  </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent
                                  className="bg-[#1c1c24] border-white/[0.08] min-w-[120px]"
                                  align="start"
                                >
                                  {TONE_OPTIONS.map((tone) => (
                                    <DropdownMenuItem
                                      key={tone.value}
                                      className={`text-xs cursor-pointer ${
                                        account.tone_preset === tone.value
                                          ? "text-zinc-100 font-semibold"
                                          : "text-zinc-400"
                                      }`}
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        onUpdateTone(account.id, tone.value);
                                      }}
                                      data-testid={`tone-option-${tone.value}-${account.id}`}
                                    >
                                      {tone.label}
                                      {account.tone_preset === tone.value && (
                                        <span className="ml-auto text-zinc-500">&#10003;</span>
                                      )}
                                    </DropdownMenuItem>
                                  ))}
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </div>
                          </div>
                        ))}
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              onClick={() =>
                                onConnectAccount(platform.platform)
                              }
                              className="w-full flex items-center gap-2 px-2 py-1.5 text-xs text-zinc-600 hover:text-zinc-300 transition-all duration-200 hover:bg-white/[0.04]"
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
        <div className="px-6 py-4 border-t border-white/[0.06]">
          <p className="text-[10px] tracking-[0.15em] uppercase text-zinc-700 font-bold">
            Comment Reply Manager
          </p>
        </div>
      </aside>
    </TooltipProvider>
  );
}
