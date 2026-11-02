"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  TrendingUp,
  PieChart,
  Layers,
  UserCheck,
  Bot,
  Settings,
  ShieldCheck,
  Wallet,
  Landmark,
  Target,
  Car,
  Sliders,
  ReceiptText,
  Calculator,
  Newspaper,
} from "lucide-react";

import { useAuth } from "@/lib/AuthContext";
import { LogIn, LogOut, UserPlus } from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const mutualFundNav = [
    { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { label: "Mutual Funds", href: "/mutual-funds", icon: TrendingUp },
    { label: "Portfolio", href: "/portfolio", icon: PieChart },
    { label: "Overlap Analysis", href: "/portfolio/overlap", icon: Layers },
    { label: "MF AI Chat", href: "/chat", icon: Bot },
  ];

  const personalFinanceNav = [
    { label: "Financial Health", href: "/finance", icon: Wallet },
    { label: "Income & Expenses", href: "/finance/profile", icon: Landmark },
    { label: "Financial Goals", href: "/finance/goals", icon: Target },
    { label: "Car Affordability", href: "/finance/affordability", icon: Car },
    { label: "What-If Simulator", href: "/finance/scenarios", icon: Sliders },
    { label: "PF AI Chat", href: "/finance/chat", icon: Bot },
  ];

  const taxNav = [
    { label: "Tax & Calculator", href: "/tax", icon: Calculator },
    { label: "Tax AI Chat", href: "/tax/chat", icon: Bot },
  ];

  return (
    <aside className="w-60 bg-surface border-r border-border min-h-screen flex flex-col justify-between p-4 text-slate-300 shrink-0 select-none">
      <div>
        {/* Logo & Platform Badge */}
        <div className="flex items-center gap-3 px-2 py-2.5 mb-4 border-b border-border/80">
          <div className="w-10 h-10 rounded-xl bg-slate-900 border border-slate-800 p-1.5 flex items-center justify-center shrink-0">
            <img src="/logo.png" alt="ArthaAI Logo" className="w-full h-full object-contain" />
          </div>
          <div>
            <h1 className="font-extrabold text-base tracking-tight text-white leading-tight">ArthaAI</h1>
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
              <ShieldCheck className="w-2.5 h-2.5" /> Multi-Agent AI
            </span>
          </div>
        </div>

        {/* Section 1: Personal Finance AI */}
        <div className="mb-3">
          <span className="px-3 text-[10px] uppercase font-bold tracking-wider text-emerald-400 block mb-1">
            Personal Finance AI
          </span>
          <nav className="space-y-0.5">
            {personalFinanceNav.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-emerald-500/10 text-emerald-400 border-l-2 border-emerald-500"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Section 2: Tax AI */}
        <div className="mb-3">
          <span className="px-3 text-[10px] uppercase font-bold tracking-wider text-purple-400 block mb-1">
            Tax AI
          </span>
          <nav className="space-y-0.5">
            {taxNav.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-purple-500/10 text-purple-400 border-l-2 border-purple-500"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-purple-400" : "text-slate-400"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Section 3: News & Research */}
        <div className="mb-3">
          <span className="px-3 text-[10px] uppercase font-bold tracking-wider text-amber-400 block mb-1">
            News &amp; Research
          </span>
          <nav className="space-y-0.5">
            {[{ label: "News & Research", href: "/research", icon: Newspaper }].map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-amber-500/10 text-amber-400 border-l-2 border-amber-500"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-amber-400" : "text-slate-400"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Section 4: Mutual Fund AI */}
        <div>
          <span className="px-3 text-[10px] uppercase font-bold tracking-wider text-blue-400 block mb-1">
            Mutual Fund AI
          </span>
          <nav className="space-y-0.5">
            {mutualFundNav.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    isActive
                      ? "bg-blue-500/10 text-blue-400 border-l-2 border-blue-500"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Bottom Profile & Settings */}
      <div className="space-y-2 pt-3 border-t border-border/80">
        <Link
          href="/onboarding"
          className="flex items-center gap-2.5 px-3 py-1.5 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-100 hover:bg-slate-800/40 transition-all"
        >
          <UserCheck className="w-3.5 h-3.5 text-slate-400" />
          Financial Onboarding
        </Link>

        {user ? (
          <div className="flex items-center justify-between p-2 rounded-xl bg-card border border-border/60">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-7 h-7 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs shrink-0">
                {user.full_name ? user.full_name.charAt(0).toUpperCase() : "U"}
              </div>
              <div className="overflow-hidden">
                <h4 className="font-bold text-xs text-white truncate">{user.full_name || "User"}</h4>
                <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-rose-400 rounded-lg transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2 pt-1">
            <Link
              href="/login"
              className="flex items-center justify-center gap-1 py-1.5 px-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-all border border-border/80"
            >
              <LogIn className="w-3 h-3" /> Login
            </Link>
            <Link
              href="/signup"
              className="flex items-center justify-center gap-1 py-1.5 px-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-600 text-slate-950 transition-all shadow-sm"
            >
              <UserPlus className="w-3 h-3" /> Sign Up
            </Link>
          </div>
        )}
      </div>
    </aside>
  );
}
