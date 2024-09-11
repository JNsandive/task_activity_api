import requests


def notify_webhook(event: str, task_name: str):
    payload = {
        "category": "TaskActivity",
        "object_type": "Task",
        "name": task_name,
        "action": event,
        "event": f"Task {task_name} {event} Successfully"
    }
    webhook_url = "https://your-webhook-url.com"
    requests.post(webhook_url, json=payload)
