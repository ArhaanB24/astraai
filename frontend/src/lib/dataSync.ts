"use client";

import { useEffect, useRef, useCallback } from "react";

export type DataSyncScope = "portfolio" | "finance" | "tax" | "goals" | "all" | string;

interface MutationEventDetail {
  scope: DataSyncScope;
  timestamp: number;
}

const EVENT_NAME = "arthaai_data_mutation";
const BROADCAST_CHANNEL_NAME = "arthaai_sync_channel";

/**
 * Global helper to notify all pages, components, and open tabs that financial data has mutated.
 * This triggers an immediate, zero-latency re-fetch on all active screens.
 */
export function notifyDataMutation(scope: DataSyncScope = "all") {
  if (typeof window === "undefined") return;

  const detail: MutationEventDetail = {
    scope,
    timestamp: Date.now(),
  };

  // 1. Dispatch in-window CustomEvent
  window.dispatchEvent(new CustomEvent(EVENT_NAME, { detail }));

  // 2. Broadcast across browser tabs via BroadcastChannel if supported
  try {
    if ("BroadcastChannel" in window) {
      const channel = new BroadcastChannel(BROADCAST_CHANNEL_NAME);
      channel.postMessage(detail);
      channel.close();
    }
  } catch {
    // BroadcastChannel fallback silently ignored if restricted in iframe
  }
}

export interface AutoRefreshOptions {
  /**
   * Polling interval in milliseconds. Defaults to 4000ms (4 seconds).
   * Set to 0 or null to disable periodic timer polling.
   */
  intervalMs?: number;
  /**
   * Whether auto-refresh is active (e.g. only when user is authenticated).
   * Defaults to true.
   */
  enabled?: boolean;
  /**
   * Array or string of mutation event scopes to listen to.
   * Defaults to ["all"] which reacts to any mutation.
   */
  eventScopes?: DataSyncScope | DataSyncScope[];
  /**
   * Immediately re-fetch when the window/tab gains focus.
   * Defaults to true.
   */
  refreshOnFocus?: boolean;
  /**
   * Immediately re-fetch when the document transitions to visible.
   * Defaults to true.
   */
  refreshOnVisible?: boolean;
  /**
   * Run fetch immediately on mount. Defaults to true.
   */
  fetchOnMount?: boolean;
}

/**
 * Universal Auto-Refresh & Real-Time Polling Hook.
 * Automatically keeps all data on the page fresh through:
 * 1. Background periodic polling
 * 2. Window focus & document visibility sync
 * 3. Instant zero-latency mutation event triggers (in-tab & cross-tab)
 */
export function useAutoRefresh(
  fetcher: () => void | Promise<void>,
  options: AutoRefreshOptions = {}
) {
  const {
    intervalMs = 4000,
    enabled = true,
    eventScopes = "all",
    refreshOnFocus = true,
    refreshOnVisible = true,
    fetchOnMount = true,
  } = options;

  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const isFetchingRef = useRef(false);
  const lastFetchTimeRef = useRef(0);

  const safeFetch = useCallback(async () => {
    // Prevent overlapping parallel fetches
    if (isFetchingRef.current) return;
    
    // Throttle duplicate triggers within 300ms
    const now = Date.now();
    if (now - lastFetchTimeRef.current < 300) return;

    try {
      isFetchingRef.current = true;
      lastFetchTimeRef.current = now;
      await fetcherRef.current();
    } catch (err) {
      console.warn("Auto-refresh fetch failed:", err);
    } finally {
      isFetchingRef.current = false;
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    // 1. Initial Mount Fetch
    if (fetchOnMount) {
      safeFetch();
    }

    // 2. Periodic Interval Polling (only runs when tab is visible)
    let timer: NodeJS.Timeout | null = null;
    if (intervalMs && intervalMs > 0) {
      timer = setInterval(() => {
        if (typeof document !== "undefined" && document.visibilityState === "hidden") {
          return; // Skip background polling when tab is hidden
        }
        safeFetch();
      }, intervalMs);
    }

    // 3. Focus & Visibility Sync Listeners
    const handleFocus = () => {
      if (refreshOnFocus) safeFetch();
    };

    const handleVisibilityChange = () => {
      if (refreshOnVisible && document.visibilityState === "visible") {
        safeFetch();
      }
    };

    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    // 4. In-Window Mutation Listener
    const scopesList = Array.isArray(eventScopes) ? eventScopes : [eventScopes];
    const handleLocalMutation = (e: Event) => {
      const customEvent = e as CustomEvent<MutationEventDetail>;
      const scope = customEvent.detail?.scope;
      if (!scope || scopesList.includes("all") || scopesList.includes(scope) || scope === "all") {
        safeFetch();
      }
    };
    window.addEventListener(EVENT_NAME, handleLocalMutation);

    // 5. Cross-Tab Broadcast Channel Listener
    let channel: BroadcastChannel | null = null;
    try {
      if ("BroadcastChannel" in window) {
        channel = new BroadcastChannel(BROADCAST_CHANNEL_NAME);
        channel.onmessage = (event) => {
          const scope = event.data?.scope;
          if (!scope || scopesList.includes("all") || scopesList.includes(scope) || scope === "all") {
            safeFetch();
          }
        };
      }
    } catch {
      // Ignored
    }

    return () => {
      if (timer) clearInterval(timer);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener(EVENT_NAME, handleLocalMutation);
      if (channel) {
        channel.close();
      }
    };
  }, [enabled, intervalMs, refreshOnFocus, refreshOnVisible, fetchOnMount, eventScopes, safeFetch]);
}
