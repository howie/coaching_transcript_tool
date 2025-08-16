#\!/usr/bin/env python3
"""
測試轉檔流程以確認 Celery 和 Google STT 是否正常工作
"""
import sys
import os
import time
from datetime import datetime

sys.path.append('packages/core-logic/src')

# 設定環境變數
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://coach_user:coach_pass_dev@localhost:5432/coaching_assistant_dev')
os.environ['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://:redis_pass_dev@localhost:6379/0')

from coaching_assistant.core.database import get_db_session
from coaching_assistant.models.session import Session, SessionStatus
from coaching_assistant.tasks.transcription_tasks import transcribe_audio
from coaching_assistant.core.celery_app import celery_app

def check_celery_connection():
    """檢查 Celery 連接"""
    try:
        # 測試 Celery 連接
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            print("✅ Celery is connected")
            for worker, info in stats.items():
                print(f"  Worker: {worker}")
            return True
        else:
            print("❌ No Celery workers found. Please start a worker with:")
            print("   celery -A coaching_assistant.core.celery_app worker --loglevel=info")
            return False
    except Exception as e:
        print(f"❌ Celery connection failed: {e}")
        return False

def check_recent_sessions():
    """檢查最近的轉檔 sessions"""
    with get_db_session() as db:
        recent_sessions = db.query(Session).order_by(Session.created_at.desc()).limit(5).all()
        
        if recent_sessions:
            print("\n📋 Recent Transcription Sessions:")
            print("-" * 50)
            for session in recent_sessions:
                print(f"ID: {session.id}")
                print(f"  Status: {session.status.value}")
                print(f"  Audio: {session.audio_filename or 'No file'}")
                print(f"  Job ID: {session.transcription_job_id or 'No job'}")
                print(f"  Created: {session.created_at}")
                print()
        else:
            print("\n⚠️  No transcription sessions found")
        
        return recent_sessions

def monitor_task(task_id, timeout=30):
    """監控 Celery 任務狀態"""
    print(f"\n🔍 Monitoring task {task_id}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        result = celery_app.AsyncResult(task_id)
        
        print(f"  Status: {result.status}")
        
        if result.ready():
            if result.successful():
                print(f"  ✅ Task completed successfully")
                print(f"  Result: {result.result}")
            else:
                print(f"  ❌ Task failed: {result.info}")
            break
        
        time.sleep(2)
    else:
        print(f"  ⏱️  Task still running after {timeout} seconds")

def main():
    print("🎯 Transcription Flow Test")
    print("=" * 50)
    
    # 1. 檢查 Celery
    if not check_celery_connection():
        return
    
    # 2. 檢查最近的 sessions
    sessions = check_recent_sessions()
    
    # 3. 如果有 pending 的 session，嘗試觸發轉檔
    if sessions:
        for session in sessions:
            if session.status == SessionStatus.PENDING and session.gcs_audio_path:
                print(f"\n🚀 Found pending session {session.id}")
                print(f"   Audio path: {session.gcs_audio_path}")
                
                response = input("   Start transcription? (y/n): ")
                if response.lower() == 'y':
                    # 發送轉檔任務
                    task = transcribe_audio.delay(
                        str(session.id),
                        session.gcs_audio_path,
                        session.language
                    )
                    print(f"   📤 Task sent: {task.id}")
                    
                    # 監控任務
                    monitor_task(task.id)
                break

if __name__ == "__main__":
    main()
