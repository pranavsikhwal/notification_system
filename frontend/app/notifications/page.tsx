"use client";

import { useEffect, useState } from "react";

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

  const userId = 1;

  async function fetchNotifications(): Promise<void> {
    const res = await fetch(
      `http://127.0.0.1:8000/notifications?user_id=${userId}`,
    );
    const data: Notification[] = await res.json();
    setNotifications(data);
    setLoading(false);
  }

  useEffect(() => {
    fetchNotifications();

    // Open WebSocket connection when the page loads
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws/${userId}`); //not hhtps use ws .

    ws.onopen = () => {
      setConnected(true);
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const newNotification: Notification = JSON.parse(event.data);
      // Prepend new notification to the top of the list
      setNotifications((prev) => [newNotification, ...prev]);
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("WebSocket disconnected");
    };

    // Cleanup: close the connection when the component unmounts
    return () => {
      ws.close();
    };
  }, []);

  async function markAsRead(id: number): Promise<void> {
    await fetch(`http://127.0.0.1:8000/notifications/${id}/read`, {
      method: "PATCH",
    });
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
    );
  }

  if (loading) return <p className="p-6">Loading...</p>;

  return (
    <div className="max-w-lg mx-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl mr-2 font-semibold">Notifications</h1>
        <span
          className={`text-xs px-2 py-1 rounded-full ${
            connected
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {connected ? "Live" : "Disconnected"}
        </span>
      </div>
      <div className=" space-y-2">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`p-4 rounded-lg border ${
              n.is_read ? "bg-white" : "bg-blue-50 border-blue-200"
            }`}
          >
            <p className="text-sm  ">{n.message}</p>
            <div className="flex justify-between items-center mt-2">
              <span className="text-xs text-gray-700">{n.type}</span>
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
    </div>
  );
}
