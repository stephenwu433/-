"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { getUnreadCount } from "@/lib/notifications-api";

export function NotificationsNavLink() {
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const [count, setCount] = useState(0);

  const refresh = useCallback(async () => {
    if (!isLoaded || !isSignedIn) {
      setCount(0);
      return;
    }
    try {
      const token = await getToken();
      if (!token) return;
      const payload = await getUnreadCount(token);
      setCount(payload.unread_count);
    } catch {
      // keep previous count
    }
  }, [getToken, isLoaded, isSignedIn]);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 30000);
    return () => window.clearInterval(id);
  }, [refresh]);

  if (!isLoaded || !isSignedIn) return null;

  return (
    <Link
      href="/notifications"
      className="relative rounded-md px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100"
    >
      站内提醒
      {count > 0 ? (
        <span className="absolute -right-0.5 -top-0.5 inline-flex min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-semibold leading-4 text-white">
          {count > 99 ? "99+" : count}
        </span>
      ) : null}
    </Link>
  );
}
