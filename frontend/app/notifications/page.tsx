"use client";

import { useEffect, useState } from "react";

// This type should mirror your backend's NotificationOut schema exactly
interface Notification {
  id: number;
  user_id: number;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string; // dates come over JSON as strings, not Date objects
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

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
  }, []);

  async function markAsRead(id: number): Promise<void> {
    await fetch(`http://127.0.0.1:8000/notifications/${id}/read`, {
      method: "PATCH",
    });
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
    );
  } //This function tells the backend to mark a notification as read, then updates the frontend state so the user immediately sees it as read without refreshing the page.

  if (loading) return <p className="p-6">Loading...</p>;

  return (
    <div className="max-w-lg mx-auto p-6">
      <h1 className="text-xl font-semibold mb-4">Notifications</h1>
      <div className="space-y-2">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`p-4 rounded-lg border ${
              n.is_read ? "bg-black" : " border-blue-600"
            }`}
          >
            <p className="text-sm text-white-600">{n.message}</p>
            <div className="flex justify-between items-center mt-2">
              <span className="text-xs text-gray-300">{n.type}</span>
              {!n.is_read && (
                <button
                  onClick={() => markAsRead(n.id)}
                  className=" ml-2 text-xs text-blue-600 hover:underline"
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
