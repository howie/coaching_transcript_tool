#!/usr/bin/env python3
"""
資料庫模型驗證腳本
測試資料庫連接和模型表格建立
"""

import sys

sys.path.insert(0, "packages/core-logic/src")

try:
    from sqlalchemy import create_engine, text

    from coaching_assistant.models import (
        Base,
        Session,
        SessionRole,
        TranscriptSegment,
        User,
    )
    from coaching_assistant.models.session import SessionStatus
    from coaching_assistant.models.transcript import SpeakerRole
    from coaching_assistant.models.user import UserPlan

    print("✅ 成功匯入所有模型")

    # 測試資料庫連接
    DATABASE_URL = (
        "postgresql://coach_user:coach_pass_dev@localhost:5432/coaching_assistant_dev"
    )

    print(f"🔌 連接資料庫: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)

    # 測試連接
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✅ 資料庫連接成功: {version}")

    # 建立所有表格
    print("🏗️ 建立資料庫表格...")
    Base.metadata.create_all(engine)
    print("✅ 所有表格建立成功")

    # 檢查建立的表格
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
            )
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"📋 建立的表格: {', '.join(tables)}")

    # 測試模型關係
    print("\n🧪 測試模型功能...")

    # 測試 User 模型
    print(f"👤 User 表名: {User.__table__.name}")
    print(f"👤 User 欄位: {list(User.__table__.columns.keys())}")

    # 測試 Session 模型
    print(f"🎯 Session 表名: {Session.__table__.name}")
    print(f"🎯 Session 欄位: {list(Session.__table__.columns.keys())}")

    # 測試 TranscriptSegment 模型
    print(f"📝 TranscriptSegment 表名: {TranscriptSegment.__table__.name}")
    print(
        f"📝 TranscriptSegment 欄位: {list(TranscriptSegment.__table__.columns.keys())}"
    )

    # 測試 SessionRole 模型
    print(f"🎭 SessionRole 表名: {SessionRole.__table__.name}")
    print(f"🎭 SessionRole 欄位: {list(SessionRole.__table__.columns.keys())}")

    # 測試枚舉值
    print(f"\n📊 UserPlan 選項: {[plan.value for plan in UserPlan]}")
    print(f"📊 SessionStatus 選項: {[status.value for status in SessionStatus]}")
    print(f"📊 SpeakerRole 選項: {[role.value for role in SpeakerRole]}")

    print("\n🎉 所有驗證測試通過！")

except Exception as e:
    print(f"❌ 驗證失敗: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
