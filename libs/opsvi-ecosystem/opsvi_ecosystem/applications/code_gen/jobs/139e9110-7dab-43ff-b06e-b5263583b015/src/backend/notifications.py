"""
Notification manager for sending real-time events (via WebSocket manager or push/email as needed).
"""
import logging


def send_notification(user_id: str, message: str, meta: dict = None):
    # Placeholder: Actual implementation could be WebSockets, emails, or push
    logging.info(f"Notify {user_id}: {message} | {meta}")


class NotificationManager:
    def notify_task_update(self, user_id: str, task_id: str, event: str):
        send_notification(user_id, f"Task {task_id} {event}", {"task_id": task_id})

    def notify_comment(self, user_id: str, comment_id: str):
        send_notification(
            user_id, f"New comment ({comment_id})", {"comment_id": comment_id}
        )


notification_manager = NotificationManager()
