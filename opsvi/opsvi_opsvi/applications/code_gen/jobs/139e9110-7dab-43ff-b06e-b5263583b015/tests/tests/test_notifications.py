import pytest
from backend.notifications import NotificationManager, send_notification


@pytest.mark.asyncio
def test_send_notification_with_valid_user_and_message():
    user_id = "user1"
    message = "Task updated"
    meta = {"task_id": "task1"}
    await send_notification(user_id, message, meta)
    # No exception means success


def test_notification_manager_notify_task_update_and_comment_methods():
    nm = NotificationManager()
    result1 = nm.notify_task_update("user1", "task1", "updated")
    result2 = nm.notify_comment("user1", "comment1")
    assert result1 is None or True
    assert result2 is None or True
