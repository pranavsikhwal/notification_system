"use client";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const WS_URL = API_URL?.replace("http", "ws");

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";

interface Notification {
  id: number;
  user_id: number;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [connected, setConnected] = useState<boolean>(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState<boolean>(false);
  const router = useRouter();
  const wsRef = useRef<WebSocket | null>(null);
  const [cursor, setCursor] = useState<number | null>(null);
  const [hasMore, setHasMore] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const isUnmountingRef = useRef(false);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  async function fetchNotifications(
    token: string,
    before?: number,
  ): Promise<void> {
    const url = before
      ? `${API_URL}/notifications?before_id=${before}&limit=20`
      : `${API_URL}/notifications?limit=20`;
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (res.status === 401) {
      router.push("/login");
      return;
    }

    const data: Notification[] = await res.json();

    if (before) {
      setNotifications((prev) => [...prev, ...data]); // append for "load more"
    } else {
      setNotifications(data); // replace for initial load
    }

    if (data.length < 20) {
      setHasMore(false); // fewer than a full page = no more left
    }

    if (data.length > 0) {
      setCursor(data[data.length - 1].id); // last item's id becomes next cursor
    }

    setLoading(false);
    setLoadingMore(false);
  }

  const reconnectAttemptsRef = useRef<number>(0); //useref survives re render
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );

  function connectWebSocket(token: string) {
    const ws = new WebSocket(`${WS_URL}/ws?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectAttemptsRef.current = 0;
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const newNotification: Notification = JSON.parse(event.data);
      setNotifications((prev) => [newNotification, ...prev]);
    };

    ws.onclose = () => {
      setConnected(false);

      if (isUnmountingRef.current) {
        console.log("WebSocket closed intentionally, not reconnecting");
        return;
      }

      console.log("WebSocket disconnected, scheduling reconnect...");
      const attempt = reconnectAttemptsRef.current;
      const delay = Math.min(1000 * 2 ** attempt, 30000);

      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttemptsRef.current += 1;
        connectWebSocket(token);
      }, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    isUnmountingRef.current = false;
    fetchNotifications(token);
    connectWebSocket(token);

    return () => {
      isUnmountingRef.current = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, []);

  async function markAsRead(id: number): Promise<void> {
    const token = localStorage.getItem("access_token");
    await fetch(`${API_URL}/notifications/${id}/read`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });

    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
    );
  }

  function confirmLogout() {
    isUnmountingRef.current = true;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    localStorage.removeItem("access_token");
    router.push("/login");
  }

  async function handleLoadMore() {
    const token = localStorage.getItem("access_token");
    if (!token || cursor === null) return;
    setLoadingMore(true);
    await fetchNotifications(token, cursor);
  }

  if (loading) return <p className="p-6">Loading...</p>;

  return (
    <div className="max-w-lg mx-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">Notifications</h1>
          {unreadCount > 0 && (
            <span className="bg-red-500 text-white text-xs font-medium px-2 py-0.5 rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`text-xs px-2 py-1 rounded-full ${
              connected
                ? "bg-green-100 text-green-700"
                : "bg-red-100 text-red-700"
            }`}
          >
            {connected ? "Live" : "Disconnected"}
          </span>
          <button
            onClick={() => setShowLogoutConfirm(true)}
            className="text-xs text-gray-500 border rounded-lg px-3 py-1 hover:bg-gray-50"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`p-4 rounded-lg border ${
              n.is_read ? "bg-white" : "bg-blue-50 border-blue-200"
            }`}
          >
            <p className="text-sm">{n.message}</p>
            <div className="flex justify-between items-center mt-2">
              <span className="text-xs text-gray-400">{n.type}</span>
              {!n.is_read && (
                <button
                  onClick={() => markAsRead(n.id)}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Mark as read
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      {hasMore && (
        <button
          onClick={handleLoadMore}
          disabled={loadingMore}
          className="w-full mt-3 text-sm text-blue-600 hover:underline disabled:text-gray-400"
        >
          {loadingMore ? "Loading..." : "Load more"}
        </button>
      )}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-80 shadow-lg">
            <h2 className="text-lg font-semibold mb-2">Log out?</h2>
            <p className="text-sm text-gray-500 mb-4">
              You'll need to log in again to see your notifications.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowLogoutConfirm(false)}
                className="text-sm px-4 py-2 rounded-lg border hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmLogout}
                className="text-sm px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700"
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
