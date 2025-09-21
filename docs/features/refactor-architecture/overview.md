# Clean Architecture Refactoring - 架構原則與設計

**Last Updated**: 2025-09-21
**Focus**: 重構過程中確立的架構原則和設計模式

## 核心架構轉換

### 重構目標
將 legacy monolithic codebase 轉換為可維護、可測試的 Clean Architecture，實現關注點分離和依賴反轉。

**From**: API 端點直接使用 SQLAlchemy，業務邏輯混雜
**To**: 清楚的層級分離和依賴注入模式

## Clean Architecture Lite 原則

### 1. **三層架構分離**
```
🌐 API Layer (HTTP Interface)
    ↓ (Dependency Injection)
🏛️ Core Layer (Business Logic)
    ↓ (Repository Ports)
🔧 Infrastructure Layer (External Concerns)
```

### 2. **依賴方向法則 (Dependency Direction Rule)**
- **Core** 永遠不依賴 Infrastructure
- **Infrastructure** 實作 Core 介面
- **API** 只依賴 Core 抽象化

### 3. **Clean Architecture Lite 實用主義**
- 遷移期間保留 Legacy ORM models 以確保相容性
- Domain ↔ ORM 轉換在 Infrastructure layer 處理
- 漸進式遷移方法以維持系統穩定性

## 架構規則與設計模式

### 🚫 **嚴格規則（絕不違反）**

1. **Core Services**: 零 SQLAlchemy imports 或 Session 依賴
2. **API Layer**: 只處理 HTTP 關注點，不包含業務邏輯或直接 DB 存取
3. **Repository Pattern**: 所有資料存取透過 repository ports
4. **依賴方向**: Core ← Infrastructure，永不逆轉

### ✅ **必要模式**

1. **Use Cases**: 單一職責業務邏輯，使用依賴注入
2. **Repository Ports**: 抽象介面定義資料存取合約
3. **Factory Pattern**: 依賴注入實現乾淨的物件創建
4. **Domain Models**: 純粹業務實體，不含基礎設施關注點

### ⚠️ **允許的 Legacy 例外**

- **有限的 Legacy Services**: `admin_daily_report.py`, `ecpay_service.py` (標記待移除)
- **Legacy API 端點**: 88 個端點仍使用 `Depends(get_db)` (數量遞減中)
- **ORM 橋接**: 在 repository 實作中處理 Domain ↔ Legacy ORM 轉換

## 檔案組織結構

```
src/coaching_assistant/
├── core/                     # 🏛️ 業務邏輯層 (Pure Domain)
│   ├── models/              # 領域實體 (dataclasses)
│   ├── repositories/        # Repository ports (interfaces)
│   └── services/            # 用例 (business logic)
├── infrastructure/          # 🔧 基礎設施層
│   ├── db/repositories/     # SQLAlchemy 實作
│   ├── db/session.py        # 資料庫會話管理
│   ├── factories.py         # 依賴注入
│   └── memory_repositories.py # 測試實作
└── api/                     # 🌐 HTTP 介面層
    ├── v1/                  # FastAPI 端點
    ├── schemas/             # 請求/回應 DTOs
    └── dependencies.py      # DI 容器設定
```

## 設計模式應用

### 1. **Repository Pattern**
```python
# ✅ 正確：透過 Port 定義合約
class SessionRepoPort(Protocol):
    def get_by_id(self, session_id: str) -> Session: ...
    def save(self, session: Session) -> None: ...

# ✅ 正確：Infrastructure 實作 Port
class SQLAlchemySessionRepository:
    def get_by_id(self, session_id: str) -> Session:
        orm_session = self.db.query(SessionModel).filter_by(id=session_id).first()
        return self._to_domain(orm_session)
```

### 2. **Dependency Injection Pattern**
```python
# ✅ 正確：Use Case 接受 Port 注入
class SessionCreationUseCase:
    def __init__(self, session_repo: SessionRepoPort, user_repo: UserRepoPort):
        self.session_repo = session_repo
        self.user_repo = user_repo

# ✅ 正確：Factory 組裝依賴
def create_session_use_case() -> SessionCreationUseCase:
    return SessionCreationUseCase(
        session_repo=create_session_repository(),
        user_repo=create_user_repository()
    )
```

### 3. **Use Case Pattern**
```python
# ✅ 正確：單一職責，純業務邏輯
class SessionCreationUseCase:
    def execute(self, request: CreateSessionRequest) -> CreateSessionResponse:
        # 1. 驗證業務規則
        user = self.user_repo.get_by_id(request.user_id)
        self._validate_plan_limits(user)

        # 2. 執行業務邏輯
        session = Session.create(title=request.title, user_id=user.id)

        # 3. 持久化
        self.session_repo.save(session)

        return CreateSessionResponse(session_id=session.id)
```

## 測試策略

### Unit Tests (快速，隔離)
```python
def test_session_creation_with_plan_limits():
    # 使用 in-memory repositories
    user_repo = InMemoryUserRepository([user_with_free_plan])
    session_repo = InMemorySessionRepository()

    use_case = SessionCreationUseCase(session_repo, user_repo)

    # 測試業務邏輯
    with pytest.raises(PlanLimitExceededException):
        use_case.execute(CreateSessionRequest(user_id=user.id))
```

### Integration Tests (資料庫)
```python
def test_session_repository_integration(db_session):
    repo = SQLAlchemySessionRepository(db_session)

    session = Session.create(title="Test", user_id="123")
    repo.save(session)

    retrieved = repo.get_by_id(session.id)
    assert retrieved.title == "Test"
```

## 重構效益

### 📈 **技術效益**
- **可維護性**: 業務規則集中在 use cases
- **可測試性**: 純領域邏輯可無資料庫測試
- **擴展性**: 清楚介面便於技術替換
- **團隊協作**: 清楚架構降低新成員學習成本

### 🎯 **業務價值**
- **開發速度**: 清楚模式加速功能開發
- **錯誤減少**: 層級隔離防止跨層失效
- **未來保障**: 乾淨介面便於技術演進

這次重構建立了堅實的基礎，在維持系統穩定的同時，持續交付業務價值。