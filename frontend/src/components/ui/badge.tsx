import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "emerald" | "amber" | "blue";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    secondary: "bg-slate-800 text-slate-300 border-slate-700",
    destructive: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    outline: "text-slate-300 border-border",
    emerald: "bg-emerald-950/60 text-emerald-400 border-emerald-800/40",
    amber: "bg-amber-950/60 text-amber-300 border-amber-800/40",
    blue: "bg-blue-950/60 text-blue-400 border-blue-800/40",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-lg border px-2 py-0.5 text-[10px] font-bold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variantStyles[variant] || variantStyles.default,
        className
      )}
      {...props}
    />
  );
}

export { Badge };
