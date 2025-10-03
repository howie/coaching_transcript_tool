# 價格方案技術變更規格

## 💰 項目 9: 費用方案簡化完整技術影響分析

此文檔詳細分析價格方案變更對整個系統的技術影響，包括資料庫、後端邏輯、前端介面和部署考量。

---

## 📋 變更摘要

### 方案結構變更
```
變更前:
├── FREE: 10 sessions + 5 transcriptions + 200 minutes
├── PRO: 25 sessions + 50 transcriptions + 原有分鐘數
└── ENTERPRISE: 企業方案

變更後:
├── FREE: 僅 200 minutes 限制
├── STUDENT (新增): 500 minutes + 300 TWD/月
├── PRO: 僅 3000 minutes + 教練履歷功能
└── COACHING_SCHOOL (重命名): 教練學校解決方案 (隱藏)
```

### 技術影響範圍
- **資料庫 Schema**: UserPlan enum + PlanConfiguration 表
- **後端邏輯**: 使用量限制檢查邏輯
- **API 端點**: Plan 相關 API 更新
- **前端介面**: Billing 頁面 + 使用量顯示
- **Migration**: 資料遷移和用戶處理

---

## 🗄️ 資料庫層面變更

### 1. UserPlan Enum 更新

#### 1.1 Enum 定義修改
```python
# src/coaching_assistant/models/user.py
class UserPlan(enum.Enum):
    """User subscription plans."""
    
    FREE = "free"
    STUDENT = "student"        # 新增
    PRO = "pro"
    ENTERPRISE = "enterprise"  # 保留（向下相容）
    COACHING_SCHOOL = "coaching_school"  # 新增（取代 ENTERPRISE）
```

#### 1.2 Alembic Migration
```python
# alembic/versions/xxxx_add_student_plan_update_limits.py
"""Add STUDENT plan and update pricing limits

Revision ID: xxxx
Revises: previous_revision
Create Date: 2025-09-xx xx:xx:xx
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

def upgrade() -> None:
    # 1. 新增 STUDENT 到 userplan enum
    op.execute("ALTER TYPE userplan ADD VALUE 'STUDENT' AFTER 'FREE'")
    op.execute("ALTER TYPE userplan ADD VALUE 'COACHING_SCHOOL' AFTER 'ENTERPRISE'")
    
    # 2. 更新現有企業用戶至專業版（如果需要）
    op.execute("""
        UPDATE "user" 
        SET plan = 'PRO' 
        WHERE plan = 'ENTERPRISE' 
        AND created_at < NOW()
    """)
    
    # 3. 更新 plan_configurations 表（透過 seed script）
    
def downgrade() -> None:
    # 回滾邏輯
    op.execute("""
        UPDATE "user" 
        SET plan = 'ENTERPRISE' 
        WHERE plan = 'COACHING_SCHOOL'
    """)
    
    # 注意: PostgreSQL 不支援移除 enum 值，需要重建 enum
    # 這裡提供警告訊息
    print("WARNING: Cannot remove enum values in PostgreSQL. Manual cleanup required.")
```

### 2. PlanConfiguration 表更新

#### 2.1 新的 Seed Data
```python
# scripts/database/seed_updated_plan_configurations.py
def seed_updated_plan_configurations(db: Session):
    """更新方案配置的 seed 資料"""
    
    # 清空現有配置（或更新）
    db.query(PlanConfiguration).delete()
    
    # 免費版 - 簡化限制
    free_plan = PlanConfiguration(
        plan_type=UserPlan.FREE,
        plan_name="free",
        display_name="免費試用",
        description="適合初次體驗的用戶",
        tagline="開始您的教練旅程",
        limits={
            # 移除 session 和 transcription 限制
            "max_total_minutes": 200,        # 僅保留分鐘數限制
            "max_file_size_mb": 60,
            "max_recording_minutes": 60,     # 單檔最長 60 分鐘
            "export_formats": ["json", "txt"],
            "concurrent_processing": 1,
            "retention_days": 30
        },
        features={
            "priority_support": False,
            "coach_profile": False,          # 教練履歷功能
            "team_collaboration": False,
            "api_access": False,
            "advanced_analytics": False
        },
        monthly_price_cents=0,
        annual_price_cents=0,
        monthly_price_twd_cents=0,
        annual_price_twd_cents=0,
        currency="TWD",
        is_popular=False,
        is_enterprise=False,
        color_scheme="gray",
        sort_order=1,
        is_active=True,
        is_visible=True
    )
    
    # 學生輕量版 - 新增方案
    student_plan = PlanConfiguration(
        plan_type=UserPlan.STUDENT,
        plan_name="student",
        display_name="學生輕量版",
        description="專為學生設計的經濟方案",
        tagline="學習更多，花費更少",
        limits={
            "max_total_minutes": 500,        # 每月 500 分鐘
            "max_file_size_mb": 200,         # 最大檔案 200MB
            "max_recording_minutes": 60,     # 單檔最長 60 分鐘
            "export_formats": ["json", "txt", "vtt"],
            "concurrent_processing": 2,
            "retention_days": 90
        },
        features={
            "priority_support": False,
            "coach_profile": False,
            "team_collaboration": False,
            "api_access": False,
            "advanced_analytics": True,
            "student_resources": True        # 學生專屬資源
        },
        monthly_price_cents=30000,          # 300 TWD
        annual_price_cents=25000,           # 250 TWD/月 (年付)
        monthly_price_twd_cents=30000,
        annual_price_twd_cents=25000,
        currency="TWD",
        is_popular=True,                    # 標記為熱門
        is_enterprise=False,
        color_scheme="green",
        sort_order=2,
        is_active=True,
        is_visible=True,
        extra_data={
            "target_audience": "students",
            "eligibility_verification": True,  # 需要學生身份驗證
            "max_team_members": 1
        }
    )
    
    # 專業版 - 簡化並新增教練履歷
    pro_plan = PlanConfiguration(
        plan_type=UserPlan.PRO,
        plan_name="pro",
        display_name="專業版",
        description="專業教練的完整解決方案",
        tagline="專業教練的首選",
        limits={
            "max_total_minutes": 3000,       # 每月 3000 分鐘
            "max_file_size_mb": 200,
            "max_recording_minutes": 120,    # 單檔最長 2 小時
            "export_formats": ["json", "txt", "vtt", "srt", "docx"],
            "concurrent_processing": 3,
            "retention_days": 365
        },
        features={
            "priority_support": True,
            "coach_profile": True,           # 獨享教練履歷功能
            "team_collaboration": False,
            "api_access": True,
            "advanced_analytics": True,
            "custom_branding": True
        },
        monthly_price_cents=89000,          # 890 TWD
        annual_price_cents=75000,           # 750 TWD/月 (年付)
        monthly_price_twd_cents=89000,
        annual_price_twd_cents=75000,
        currency="TWD",
        is_popular=True,
        is_enterprise=False,
        color_scheme="blue",
        sort_order=3,
        is_active=True,
        is_visible=True,
        extra_data={
            "coach_profile_features": [
                "個人品牌頁面",
                "客戶評價系統", 
                "專業認證展示",
                "成功案例分享"
            ]
        }
    )
    
    # 教練學校解決方案 - 隱藏方案
    coaching_school_plan = PlanConfiguration(
        plan_type=UserPlan.COACHING_SCHOOL,
        plan_name="coaching_school",
        display_name="教練學校解決方案",
        description="為教練培訓機構設計的企業方案",
        tagline="培養下一代教練",
        limits={
            "max_total_minutes": -1,         # 無限制
            "max_file_size_mb": 500,
            "max_recording_minutes": -1,
            "export_formats": ["json", "txt", "vtt", "srt", "docx", "xlsx", "pdf"],
            "concurrent_processing": 10,
            "retention_days": -1
        },
        features={
            "priority_support": True,
            "coach_profile": True,
            "team_collaboration": True,
            "api_access": True,
            "advanced_analytics": True,
            "custom_branding": True,
            "bulk_user_management": True,
            "training_resources": True
        },
        monthly_price_cents=0,              # 聯絡報價
        annual_price_cents=0,
        monthly_price_twd_cents=0,
        annual_price_twd_cents=0,
        currency="TWD",
        is_popular=False,
        is_enterprise=True,
        color_scheme="purple",
        sort_order=4,
        is_active=True,
        is_visible=False,                   # 隱藏方案
        extra_data={
            "contact_sales": True,
            "custom_pricing": True,
            "min_seats": 10
        }
    )
    
    # 儲存所有方案
    plans = [free_plan, student_plan, pro_plan, coaching_school_plan]
    for plan in plans:
        db.add(plan)
    
    db.commit()
    logger.info("✅ Updated plan configurations seeded successfully")
```

---

## 🔧 後端邏輯變更

### 1. 使用量限制邏輯重構

#### 1.1 PlanLimits 服務更新
```python
# src/coaching_assistant/services/plan_limits.py
class PlanLimits:
    """更新後的方案限制配置"""
    
    # 簡化的限制結構
    LIMITS = {
        PlanName.FREE: PlanLimit(
            max_total_minutes=200,           # 僅保留分鐘數限制
            max_file_size_mb=60,
            max_recording_minutes=60,
            export_formats=["txt", "json"],
            concurrent_processing=1,
            retention_days=30,
            monthly_price_twd=0,
        ),
        PlanName.STUDENT: PlanLimit(        # 新增學生方案
            max_total_minutes=500,
            max_file_size_mb=200,
            max_recording_minutes=60,
            export_formats=["txt", "json", "vtt"],
            concurrent_processing=2,
            retention_days=90,
            monthly_price_twd=300,
        ),
        PlanName.PRO: PlanLimit(
            max_total_minutes=3000,
            max_file_size_mb=200,
            max_recording_minutes=120,
            export_formats=["txt", "json", "vtt", "srt", "docx"],
            concurrent_processing=3,
            retention_days=365,
            monthly_price_twd=890,
            features={"coach_profile": True},  # 專業版獨享
        ),
        PlanName.COACHING_SCHOOL: PlanLimit(
            max_total_minutes=-1,            # 無限制
            max_file_size_mb=500,
            max_recording_minutes=-1,
            export_formats=["txt", "json", "vtt", "srt", "docx", "xlsx", "pdf"],
            concurrent_processing=10,
            retention_days=-1,
            monthly_price_twd=0,             # 聯絡報價
        ),
    }
```

#### 1.2 使用量追蹤服務更新
```python
# src/coaching_assistant/services/usage_tracking.py
class UsageTrackingService:
    """簡化的使用量追蹤服務"""
    
    async def check_minutes_limit(
        self, 
        user_id: str, 
        additional_minutes: float
    ) -> tuple[bool, dict]:
        """檢查分鐘數限制（移除 session/transcription 檢查）"""
        
        user = await self.get_user_with_plan(user_id)
        plan_limits = PlanLimits.get_plan_limit(user.plan)
        
        # 僅檢查分鐘數限制
        current_usage = await self.get_monthly_usage(user_id)
        total_minutes = current_usage.total_minutes + additional_minutes
        
        if plan_limits.max_total_minutes == -1:  # 無限制
            return True, {"allowed": True}
            
        if total_minutes > plan_limits.max_total_minutes:
            return False, {
                "allowed": False,
                "limit_type": "minutes",
                "current_usage": current_usage.total_minutes,
                "limit": plan_limits.max_total_minutes,
                "additional_requested": additional_minutes
            }
        
        return True, {"allowed": True}
    
    async def record_usage(
        self, 
        user_id: str, 
        session_id: str, 
        minutes_used: float
    ):
        """記錄使用量（簡化版）"""
        
        usage_record = UsageLog(
            user_id=user_id,
            session_id=session_id,
            audio_minutes_processed=minutes_used,
            # 移除 sessions_created, transcriptions_completed 欄位
            recorded_at=datetime.utcnow()
        )
        
        await self.db.add(usage_record)
        await self.db.commit()
        
        # 更新用戶的累計使用量
        await self.update_user_total_usage(user_id, minutes_used)
```

### 2. API 端點更新

#### 2.1 Plans API 更新
```python
# src/coaching_assistant/api/v1/plans.py
@router.get("/plans")
async def get_available_plans(
    include_hidden: bool = False,
    current_user: User = Depends(get_current_user)
) -> List[PlanConfigurationResponse]:
    """獲取可用方案列表"""
    
    query = select(PlanConfiguration).where(PlanConfiguration.is_active == True)
    
    # 預設不顯示隱藏方案
    if not include_hidden:
        query = query.where(PlanConfiguration.is_visible == True)
    
    # 學生方案需要特殊處理
    plans = await db.execute(query)
    plan_list = plans.scalars().all()
    
    # 根據用戶身份過濾方案
    filtered_plans = []
    for plan in plan_list:
        if plan.plan_type == UserPlan.STUDENT:
            # 檢查學生身份驗證
            if not await verify_student_eligibility(current_user):
                continue
        filtered_plans.append(plan)
    
    return [plan.to_dict() for plan in filtered_plans]

@router.get("/current")
async def get_current_plan(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """獲取用戶當前方案和使用量"""
    
    plan_config = await get_plan_configuration(current_user.plan)
    usage = await get_monthly_usage(current_user.id)
    
    return {
        "plan": plan_config.to_dict(),
        "usage": {
            "total_minutes": usage.total_minutes,
            "minutes_limit": plan_config.limits.get("max_total_minutes", -1),
            "usage_percentage": calculate_usage_percentage(
                usage.total_minutes, 
                plan_config.limits.get("max_total_minutes", -1)
            )
        },
        "features": plan_config.features
    }
```

#### 2.2 學生身份驗證 API
```python
# src/coaching_assistant/api/v1/student_verification.py
@router.post("/verify-student")
async def verify_student_status(
    verification_data: StudentVerificationRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """驗證學生身份"""
    
    # 實作學生身份驗證邏輯
    # 可以是學生證上傳、學校 email 驗證等
    
    is_verified = await process_student_verification(
        user_id=current_user.id,
        verification_data=verification_data
    )
    
    if is_verified:
        # 更新用戶資料，標記為已驗證學生
        current_user.extra_data = {
            **current_user.extra_data,
            "student_verified": True,
            "verification_date": datetime.utcnow().isoformat()
        }
        await db.commit()
        
    return {
        "verified": is_verified,
        "eligible_for_student_plan": is_verified
    }
```

---

## 🎨 前端變更

### 1. Billing 頁面重構

#### 1.1 方案選擇器更新
```typescript
// apps/web/components/billing/PlanSelector.tsx
interface Plan {
  id: string;
  name: string;
  displayName: string;
  price: {
    monthly: number;
    annual: number;
    currency: string;
  };
  limits: {
    maxTotalMinutes: number;
    maxFileSize: number;
    maxRecordingMinutes: number;
  };
  features: string[];
  isPopular: boolean;
  isVisible: boolean;
  requiresVerification?: boolean; // 學生方案需要驗證
}

const PlanSelector: React.FC = () => {
  const { data: plans } = useQuery(['plans'], fetchAvailablePlans);
  const { user } = useAuth();
  
  const visiblePlans = plans?.filter(plan => {
    if (plan.name === 'student') {
      // 學生方案需要驗證或已是學生
      return user.studentVerified || user.plan === 'student';
    }
    return plan.isVisible;
  });

  return (
    <div className="plan-selector">
      <div className="plans-grid">
        {visiblePlans?.map(plan => (
          <PlanCard 
            key={plan.id}
            plan={plan}
            isCurrentPlan={user.plan === plan.name}
            onSelect={handlePlanSelect}
          />
        ))}
      </div>
      
      {/* 學生方案驗證提示 */}
      {!user.studentVerified && (
        <StudentVerificationPrompt />
      )}
    </div>
  );
};
```

#### 1.2 使用量顯示更新
```typescript
// apps/web/components/billing/UsageDisplay.tsx
const UsageDisplay: React.FC = () => {
  const { data: usage } = useQuery(['current-plan'], fetchCurrentPlan);
  
  if (!usage) return <LoadingSpinner />;
  
  const { plan, usage: currentUsage } = usage;
  const minutesLimit = plan.limits.max_total_minutes;
  const minutesUsed = currentUsage.total_minutes;
  
  return (
    <div className="usage-display">
      <h3>本月使用量</h3>
      
      {/* 簡化的使用量顯示 - 僅顯示分鐘數 */}
      <div className="usage-metric">
        <div className="metric-header">
          <span>音檔處理時間</span>
          <span>{minutesLimit === -1 ? '無限制' : `${minutesUsed}/${minutesLimit} 分鐘`}</span>
        </div>
        
        {minutesLimit !== -1 && (
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ 
                width: `${Math.min((minutesUsed / minutesLimit) * 100, 100)}%` 
              }}
            />
          </div>
        )}
      </div>
      
      {/* 移除 sessions 和 transcriptions 顯示 */}
      
      <div className="usage-tips">
        <p>💡 提示：僅計算音檔的實際時長，不限制會談次數</p>
      </div>
    </div>
  );
};
```

#### 1.3 學生驗證組件
```typescript
// apps/web/components/billing/StudentVerification.tsx
const StudentVerification: React.FC = () => {
  const [verificationMethod, setVerificationMethod] = useState<'email' | 'document'>('email');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const submitVerification = async (data: VerificationData) => {
    setIsSubmitting(true);
    try {
      const result = await verifyStudentStatus(data);
      if (result.verified) {
        toast.success('學生身份驗證成功！您現在可以選擇學生方案');
        // 重新載入方案列表
      } else {
        toast.error('驗證失敗，請檢查提供的資料');
      }
    } catch (error) {
      toast.error('驗證過程發生錯誤，請稍後再試');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="student-verification">
      <h3>學生身份驗證</h3>
      <p>驗證學生身份以享受學生輕量版優惠價格</p>
      
      <div className="verification-methods">
        <button 
          className={verificationMethod === 'email' ? 'active' : ''}
          onClick={() => setVerificationMethod('email')}
        >
          學校信箱驗證
        </button>
        <button 
          className={verificationMethod === 'document' ? 'active' : ''}
          onClick={() => setVerificationMethod('document')}
        >
          學生證上傳
        </button>
      </div>
      
      {verificationMethod === 'email' ? (
        <EmailVerificationForm onSubmit={submitVerification} />
      ) : (
        <DocumentVerificationForm onSubmit={submitVerification} />
      )}
    </div>
  );
};
```

### 2. i18n 翻譯更新

#### 2.1 Billing 翻譯更新
```typescript
// apps/web/lib/i18n/translations/billing.ts
export const billingTranslations = {
  zh: {
    // 方案名稱
    'billing.plans.free': '免費試用',
    'billing.plans.student': '學生輕量版',
    'billing.plans.pro': '專業版',
    'billing.plans.coachingSchool': '教練學校解決方案',
    
    // 方案描述
    'billing.plans.free.desc': '適合初次體驗的用戶',
    'billing.plans.student.desc': '專為學生設計的經濟方案',
    'billing.plans.pro.desc': '專業教練的完整解決方案',
    
    // 限制描述（簡化後）
    'billing.limits.minutes': '每月 {minutes} 分鐘',
    'billing.limits.minutesUnlimited': '無分鐘數限制',
    'billing.limits.fileSize': '檔案大小上限 {size}MB',
    
    // 移除 sessions 和 transcriptions 相關翻譯
    
    // 使用量顯示
    'billing.usage.minutes': '音檔處理時間',
    'billing.usage.minutesUsed': '已使用 {used} / {total} 分鐘',
    'billing.usage.tip': '僅計算音檔的實際時長，不限制會談次數',
    
    // 學生驗證
    'billing.student.verification': '學生身份驗證',
    'billing.student.verificationDesc': '驗證學生身份以享受優惠價格',
    'billing.student.verified': '學生身份已驗證',
    'billing.student.emailMethod': '學校信箱驗證',
    'billing.student.documentMethod': '學生證上傳',
    
    // 功能標籤
    'billing.features.coachProfile': '教練履歷功能',
    'billing.features.coachProfileDesc': '建立專業的教練個人頁面',
    'billing.features.studentResources': '學生專屬資源',
  },
  en: {
    // 對應的英文翻譯...
  }
}
```

### 3. 使用量檢查組件更新

#### 3.1 檔案上傳限制更新
```typescript
// apps/web/components/upload/AudioUploader.tsx
const AudioUploader: React.FC = () => {
  const { data: currentPlan } = useQuery(['current-plan'], fetchCurrentPlan);
  
  const validateFile = (file: File) => {
    if (!currentPlan) return false;
    
    const { limits } = currentPlan.plan;
    
    // 檢查檔案大小
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > limits.max_file_size_mb) {
      toast.error(
        `檔案大小 ${fileSizeMB.toFixed(1)}MB 超過 ${currentPlan.plan.display_name} 方案限制 ${limits.max_file_size_mb}MB`
      );
      return false;
    }
    
    // 估算音檔時長並檢查分鐘數限制
    const estimatedMinutes = estimateAudioDuration(file);
    if (limits.max_total_minutes !== -1) {
      const { usage } = currentPlan;
      if (usage.total_minutes + estimatedMinutes > limits.max_total_minutes) {
        toast.error(
          `預估處理時間 ${estimatedMinutes} 分鐘將超過本月限制。` +
          `目前已使用 ${usage.total_minutes}/${limits.max_total_minutes} 分鐘`
        );
        return false;
      }
    }
    
    return true;
  };
  
  return (
    <div className="audio-uploader">
      <div className="upload-limits">
        <p>📄 檔案大小限制: {currentPlan?.plan.limits.max_file_size_mb}MB</p>
        <p>⏱️ 單檔時長限制: {currentPlan?.plan.limits.max_recording_minutes} 分鐘</p>
        {currentPlan?.plan.limits.max_total_minutes !== -1 && (
          <p>📊 本月剩餘額度: {
            currentPlan.plan.limits.max_total_minutes - currentPlan.usage.total_minutes
          } 分鐘</p>
        )}
      </div>
      
      <FileDropzone 
        onFileSelect={handleFileSelect}
        onValidate={validateFile}
      />
    </div>
  );
};
```

---

## 🔄 資料遷移策略

### 1. 現有用戶處理

#### 1.1 企業版用戶遷移
```python
# scripts/migration/migrate_enterprise_users.py
async def migrate_enterprise_users():
    """將現有企業版用戶遷移到適當方案"""
    
    enterprise_users = await db.execute(
        select(User).where(User.plan == UserPlan.ENTERPRISE)
    )
    
    for user in enterprise_users.scalars():
        # 分析用戶使用模式決定遷移目標
        usage_stats = await analyze_user_usage(user.id)
        
        if usage_stats.avg_monthly_minutes > 3000:
            # 重度使用者建議聯繫客服
            target_plan = UserPlan.PRO  # 暫時遷移到專業版
            await send_migration_notice(user, "high_usage")
        else:
            # 一般使用者遷移到專業版
            target_plan = UserPlan.PRO
            await send_migration_notice(user, "standard")
        
        # 更新用戶方案
        user.plan = target_plan
        await db.commit()
        
        # 記錄遷移歷史
        await create_migration_record(user.id, UserPlan.ENTERPRISE, target_plan)
```

#### 1.2 使用量資料清理
```python
# scripts/migration/cleanup_usage_data.py
async def cleanup_legacy_usage_fields():
    """清理舊的使用量欄位"""
    
    # 保留歷史資料但停止更新 session_count, transcription_count
    await db.execute(
        text("""
        -- 將舊的計數欄位標記為 deprecated
        ALTER TABLE usage_logs 
        ADD COLUMN IF NOT EXISTS deprecated_session_count INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS deprecated_transcription_count INTEGER DEFAULT 0;
        
        -- 將現有資料遷移到 deprecated 欄位
        UPDATE usage_logs 
        SET deprecated_session_count = sessions_created,
            deprecated_transcription_count = transcriptions_completed
        WHERE deprecated_session_count = 0;
        """)
    )
```

### 2. 漸進式部署

#### 2.1 Feature Flag 控制
```python
# src/coaching_assistant/core/feature_flags.py
class FeatureFlags:
    NEW_PRICING_ENABLED = True
    STUDENT_PLAN_ENABLED = True
    LEGACY_LIMITS_ENABLED = False  # 關閉舊的限制檢查
    
    @classmethod
    def is_new_pricing_user(cls, user: User) -> bool:
        """判斷用戶是否使用新的定價方案"""
        # 新註冊用戶或已遷移用戶使用新方案
        migration_date = datetime(2025, 9, 15)
        return (user.created_at > migration_date or 
                user.plan in [UserPlan.STUDENT, UserPlan.COACHING_SCHOOL])
```

#### 2.2 A/B 測試
```python
# src/coaching_assistant/services/ab_testing.py
class PricingABTest:
    async def get_user_pricing_variant(self, user_id: str) -> str:
        """為用戶分配定價方案變體"""
        
        # 舊用戶維持舊方案，新用戶使用新方案
        user = await get_user(user_id)
        
        if user.created_at < datetime(2025, 9, 15):
            return "legacy_pricing"
        else:
            return "new_pricing"
```

---

## 🧪 測試策略

### 1. 單元測試

#### 1.1 方案限制測試
```python
# tests/unit/services/test_new_plan_limits.py
class TestNewPlanLimits:
    def test_free_plan_limits(self):
        """測試免費版限制"""
        limits = PlanLimits.get_plan_limit(PlanName.FREE)
        assert limits.max_total_minutes == 200
        assert limits.max_sessions == -1  # 無限制
        assert limits.max_transcriptions == -1  # 無限制
    
    def test_student_plan_limits(self):
        """測試學生版限制"""
        limits = PlanLimits.get_plan_limit(PlanName.STUDENT)
        assert limits.max_total_minutes == 500
        assert limits.monthly_price_twd == 300
    
    def test_pro_plan_features(self):
        """測試專業版功能"""
        limits = PlanLimits.get_plan_limit(PlanName.PRO)
        assert limits.features.get("coach_profile") == True
        assert limits.max_total_minutes == 3000

class TestUsageTracking:
    async def test_minutes_only_tracking(self):
        """測試僅追蹤分鐘數的邏輯"""
        service = UsageTrackingService()
        
        # 模擬用戶上傳 30 分鐘音檔
        can_proceed, result = await service.check_minutes_limit(
            user_id="test-user",
            additional_minutes=30.0
        )
        
        assert can_proceed == True
        assert result["allowed"] == True
```

#### 1.2 API 測試
```python
# tests/integration/api/test_new_pricing_api.py
class TestNewPricingAPI:
    async def test_get_available_plans(self, client, auth_headers):
        """測試新方案列表 API"""
        response = await client.get("/api/v1/plans", headers=auth_headers)
        
        assert response.status_code == 200
        plans = response.json()
        
        # 確認包含新方案
        plan_names = [plan["plan_name"] for plan in plans]
        assert "student" in plan_names
        assert "coaching_school" not in plan_names  # 隱藏方案
    
    async def test_student_verification(self, client, auth_headers):
        """測試學生驗證 API"""
        verification_data = {
            "method": "email",
            "email": "student@university.edu",
            "verification_code": "123456"
        }
        
        response = await client.post(
            "/api/v1/student-verification/verify-student",
            json=verification_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "verified" in result
```

### 2. 整合測試

#### 2.1 端到端方案變更測試
```python
# tests/e2e/test_plan_migration.py
class TestPlanMigration:
    async def test_enterprise_to_pro_migration(self):
        """測試企業版到專業版的遷移"""
        # 1. 建立企業版用戶
        user = await create_test_user(plan=UserPlan.ENTERPRISE)
        
        # 2. 執行遷移
        await migrate_enterprise_users()
        
        # 3. 驗證遷移結果
        updated_user = await get_user(user.id)
        assert updated_user.plan == UserPlan.PRO
        
        # 4. 驗證使用量限制
        limits_check = await check_user_limits(user.id)
        assert limits_check["max_total_minutes"] == 3000
```

### 3. 前端測試

#### 3.1 Billing 頁面測試
```typescript
// tests/frontend/billing.test.tsx
describe('新 Billing 頁面', () => {
  test('顯示正確的方案資訊', async () => {
    render(<BillingPage />);
    
    // 確認包含學生方案
    expect(screen.getByText('學生輕量版')).toBeInTheDocument();
    expect(screen.getByText('300 TWD/月')).toBeInTheDocument();
    
    // 確認移除了 session/transcription 限制顯示
    expect(screen.queryByText(/會談記錄.*限制/)).toBeNull();
    expect(screen.queryByText(/轉錄次數.*限制/)).toBeNull();
    
    // 確認顯示分鐘數限制
    expect(screen.getByText(/500.*分鐘/)).toBeInTheDocument();
  });
  
  test('學生驗證流程', async () => {
    const user = mockUser({ studentVerified: false });
    render(<BillingPage user={user} />);
    
    // 點擊學生方案應該顯示驗證提示
    fireEvent.click(screen.getByText('選擇學生方案'));
    expect(screen.getByText('學生身份驗證')).toBeInTheDocument();
  });
});
```

---

## 🚀 部署計劃

### 1. 分階段部署

#### 階段 1: 資料庫更新 (無停機)
```bash
# 1. 執行 migration
alembic upgrade head

# 2. 更新方案配置
python scripts/database/seed_updated_plan_configurations.py

# 3. 驗證資料完整性
python scripts/database/verify_plan_migration.py
```

#### 階段 2: 後端服務部署
```bash
# 1. 部署新的後端邏輯
# Feature flag 控制新舊邏輯切換
export NEW_PRICING_ENABLED=true

# 2. 漸進式開啟新功能
# 先針對新用戶開啟
export NEW_PRICING_NEW_USERS_ONLY=true
```

#### 階段 3: 前端更新
```bash
# 1. 部署新的前端介面
npm run build && npm run deploy

# 2. 更新 i18n 翻譯檔案
npm run i18n:build
```

#### 階段 4: 完整切換
```bash
# 1. 關閉舊的限制邏輯
export LEGACY_LIMITS_ENABLED=false

# 2. 執行現有用戶遷移
python scripts/migration/migrate_enterprise_users.py

# 3. 發送用戶通知
python scripts/notification/send_plan_update_notice.py
```

### 2. 回滾計劃

#### 緊急回滾步驟
```bash
# 1. 重新啟用舊邏輯
export NEW_PRICING_ENABLED=false
export LEGACY_LIMITS_ENABLED=true

# 2. 回滾資料庫 (如果必要)
alembic downgrade -1

# 3. 回滾前端 (如果必要)
git revert <commit-hash>
npm run deploy
```

### 3. 監控指標

#### 關鍵指標監控
```python
# 監控指標定義
pricing_migration_metrics = {
    "new_student_signups": Counter("學生方案註冊數"),
    "plan_upgrade_rate": Gauge("方案升級率"),
    "usage_pattern_changes": Histogram("使用模式變化"),
    "api_error_rate": Counter("API 錯誤率"),
    "user_satisfaction": Gauge("用戶滿意度")
}
```

---

## ⚠️ 風險與緩解

### 1. 技術風險

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 資料庫 Migration 失敗 | 高 | 低 | 完整備份 + 測試環境驗證 |
| 使用量計算錯誤 | 高 | 中 | 充分測試 + 漸進式部署 |
| 現有用戶體驗破壞 | 中 | 中 | Feature flag + A/B 測試 |
| 學生驗證系統問題 | 中 | 低 | 人工審核備案 |

### 2. 業務風險

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| 用戶流失 | 高 | 低 | 提前溝通 + 優惠過渡 |
| 收入下降 | 中 | 中 | 密切監控 + 快速調整 |
| 競爭劣勢 | 中 | 低 | 市場分析 + 價值強化 |

---

## 📊 成功指標

### KPI 指標
- **技術指標**:
  - Migration 成功率: 100%
  - API 錯誤率: < 0.1%
  - 頁面載入時間: < 2 秒
  
- **產品指標**:
  - 學生方案採用率: ≥ 30%
  - 專業版升級率: +25%
  - 用戶滿意度: ≥ 4.5/5
  
- **業務指標**:
  - 月收入成長: +15%
  - 客服工單: -40%
  - 用戶留存率: ≥ 95%

---

## 📝 交付檢查清單

### 資料庫層面
- [ ] UserPlan enum 更新
- [ ] PlanConfiguration 表更新
- [ ] Migration 腳本測試
- [ ] 種子資料更新
- [ ] 資料完整性驗證

### 後端開發
- [ ] PlanLimits 服務重構
- [ ] 使用量追蹤簡化
- [ ] API 端點更新
- [ ] 學生驗證功能
- [ ] 權限檢查更新

### 前端開發
- [ ] Billing 頁面重構
- [ ] 使用量顯示更新
- [ ] 學生驗證介面
- [ ] i18n 翻譯更新
- [ ] 響應式設計驗證

### 測試與品質
- [ ] 單元測試覆蓋率 ≥ 90%
- [ ] 整合測試完成
- [ ] E2E 測試通過
- [ ] 性能測試達標
- [ ] 安全測試完成

### 部署與監控
- [ ] 分階段部署計劃
- [ ] 回滾機制準備
- [ ] 監控指標設置
- [ ] 告警配置完成
- [ ] 文檔更新完整

---

*此技術規格為價格方案變更的完整指南，涵蓋所有技術層面的考量。請按照此規格進行實作，確保系統穩定和用戶體驗。*