"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/AuthContext";
import { Lock, Mail, User, AlertCircle, ArrowRight, Sparkles } from "lucide-react";

export default function SignupPage() {
  const { user, token, isLoading, signup } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && token && user) {
      if (user.onboarding_completed) {
        router.replace("/dashboard");
      } else {
        router.replace("/onboarding");
      }
    }
  }, [user, token, isLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }

    setSubmitting(true);
    try {
      await signup(fullName, email, password);
    } catch (err: any) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-card border border-border rounded-2xl p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 p-2 shadow-lg mb-2">
            <img src="/logo.png" alt="ArthaAI Logo" className="w-full h-full object-contain" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Create Your ArthaAI Account</h1>
          <p className="text-sm text-gray-400">Join and personalize your AI financial intelligence engines</p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs text-white">
          <div>
            <label className="block text-gray-400 mb-1.5 font-medium">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Priya Patel"
                className="w-full bg-gray-900 border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:border-emerald-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-400 mb-1.5 font-medium">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-gray-900 border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:border-emerald-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-400 mb-1.5 font-medium">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-gray-900 border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:border-emerald-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-400 mb-1.5 font-medium">Confirm Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-gray-900 border border-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:border-emerald-500 outline-none transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-emerald-500 hover:bg-emerald-600 font-bold text-white py-3 rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
          >
            {submitting ? "Creating Account..." : "Create Account & Start Onboarding"} <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="text-center pt-2 text-xs text-gray-400">
          Already have an account?{" "}
          <Link href="/login" className="text-emerald-400 hover:underline font-medium">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
