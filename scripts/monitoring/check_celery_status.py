# \!/usr/bin/env python3
import sys

sys.path.append("packages/core-logic/src")


from coaching_assistant.core.celery_app import celery_app

# 檢查已註冊的任務
print("📋 Registered Celery Tasks:")
for task_name in celery_app.tasks:
    if not task_name.startswith("celery."):
        print(f"  - {task_name}")

# 檢查活動的任務
inspect = celery_app.control.inspect()
active = inspect.active()
if active:
    print("\n🔄 Active Tasks:")
    for worker, tasks in active.items():
        print(f"  Worker: {worker}")
        for task in tasks:
            print(f"    - ID: {task['id']}")
            print(f"      Name: {task['name']}")
            print(f"      Args: {task['args']}")
else:
    print("\n⚠️  No Celery workers are currently running")

# 檢查計劃的任務
scheduled = inspect.scheduled()
if scheduled:
    print("\n⏰ Scheduled Tasks:")
    for worker, tasks in scheduled.items():
        for task in tasks:
            print(f"  - {task}")

# 檢查保留的任務
reserved = inspect.reserved()
if reserved:
    print("\n📌 Reserved Tasks:")
    for worker, tasks in reserved.items():
        for task in tasks:
            print(f"  - {task}")
