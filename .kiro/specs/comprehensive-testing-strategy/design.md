# 綜合測試策略設計文件

## 概述

本設計文件詳細說明如何為 Coaching Assistant Platform 建立完整的測試策略，涵蓋單元測試、整合測試、端到端測試和效能測試。

## 架構設計

### 測試金字塔架構

```
                    🔺 E2E Tests (少量，高價值)
                   /                        \
                  /    UI Tests (中等數量)    \
                 /                            \
                /    Integration Tests (中等)   \
               /                                \
              /        Unit Tests (大量，快速)    \
             /_____________________________________\
```

### 測試分層策略

#### 1. 單元測試層 (70% 測試覆蓋)
**目標：** 快速反饋，高覆蓋率，隔離測試

**範圍：**
- 業務邏輯函數
- 資料模型驗證
- 工具函數
- React 組件邏輯

**技術棧：**
- 後端：pytest + pytest-mock
- 前端：Jest + React Testing Library
- 資料庫：SQLite in-memory

#### 2. 整合測試層 (20% 測試覆蓋)
**目標：** 驗證服務間交互，資料流正確性

**範圍：**
- API 端點測試
- 資料庫整合
- 外部服務整合 (Google Cloud)
- Celery 任務執行

**技術棧：**
- API 測試：pytest + httpx
- 資料庫：PostgreSQL test database
- 外部服務：Mock/Stub

#### 3. 端到端測試層 (10% 測試覆蓋)
**目標：** 驗證完整用戶工作流程

**範圍：**
- 關鍵用戶路徑
- 跨瀏覽器相容性
- 效能基準測試

**技術棧：**
- Playwright (取代 Selenium)
- Docker Compose 測試環境

## 組件設計

### 1. 測試基礎設施

#### 測試環境管理
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

@pytest.fixture(scope="session")
def test_db():
    """建立測試資料庫連接"""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    
    # 建立所有表格
    Base.metadata.create_all(bind=engine)
    
    yield TestingSessionLocal
    
    # 清理
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """建立 FastAPI 測試客戶端"""
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
```

#### 測試資料工廠
```python
# tests/factories.py
import factory
from factory.alchemy import SQLAlchemyModelFactory

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    plan = UserPlan.FREE
    usage_minutes = 0

class SessionFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Session
        sqlalchemy_session_persistence = "commit"
    
    user = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence", nb_words=3)
    status = SessionStatus.PENDING
    language = "zh-TW"
```

### 2. 核心工作流程測試

#### 音頻轉錄端到端測試
```python
# tests/e2e/test_transcription_workflow.py
import pytest
from playwright.sync_api import Page, expect

class TestTranscriptionWorkflow:
    def test_complete_transcription_flow(self, page: Page):
        """測試完整的音頻轉錄工作流程"""
        # 1. 用戶登入
        page.goto("/login")
        page.fill("[data-testid=email]", "test@example.com")
        page.fill("[data-testid=password]", "password")
        page.click("[data-testid=login-button]")
        
        # 2. 建立新會話
        page.goto("/dashboard/sessions")
        page.click("[data-testid=new-session-button]")
        page.fill("[data-testid=session-title]", "Test Session")
        page.click("[data-testid=create-session]")
        
        # 3. 上傳音頻檔案
        page.set_input_files(
            "[data-testid=audio-upload]", 
            "tests/data/sample_audio.mp3"
        )
        page.click("[data-testid=upload-button]")
        
        # 4. 等待轉錄完成
        expect(page.locator("[data-testid=status]")).to_have_text(
            "Processing", timeout=5000
        )
        expect(page.locator("[data-testid=status]")).to_have_text(
            "Completed", timeout=60000
        )
        
        # 5. 驗證轉錄結果
        page.click("[data-testid=transcript-tab]")
        expect(page.locator("[data-testid=transcript-content]")).to_be_visible()
        
        # 6. 測試匯出功能
        page.click("[data-testid=export-button]")
        page.click("[data-testid=export-vtt]")
        
        # 驗證下載
        with page.expect_download() as download_info:
            page.click("[data-testid=download-link]")
        download = download_info.value
        assert download.suggested_filename.endswith(".vtt")
```

### 3. API 整合測試

#### 認證與授權測試
```python
# tests/integration/api/test_auth_integration.py
import pytest
from httpx import AsyncClient

class TestAuthIntegration:
    async def test_google_oauth_flow(self, client: AsyncClient):
        """測試 Google OAuth 認證流程"""
        # 模擬 Google OAuth 回調
        mock_token = "mock_google_token"
        
        response = await client.post(
            "/api/v1/auth/google",
            json={"id_token": mock_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
    
    async def test_jwt_token_validation(self, client: AsyncClient, auth_headers):
        """測試 JWT token 驗證"""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "name" in data
```

#### 轉錄服務整合測試
```python
# tests/integration/api/test_transcription_integration.py
import pytest
from unittest.mock import patch, AsyncMock

class TestTranscriptionIntegration:
    @patch('coaching_assistant.services.gcs_client.upload_audio')
    @patch('coaching_assistant.services.stt_client.transcribe_audio')
    async def test_transcription_service_integration(
        self, 
        mock_stt, 
        mock_gcs, 
        client: AsyncClient, 
        auth_headers
    ):
        """測試轉錄服務整合"""
        # 設置 mock
        mock_gcs.return_value = "gs://bucket/audio.mp3"
        mock_stt.return_value = AsyncMock(
            segments=[
                {"speaker_id": 1, "content": "Hello", "start_sec": 0.0, "end_sec": 1.0}
            ],
            duration=60.0
        )
        
        # 建立會話
        session_response = await client.post(
            "/api/v1/sessions",
            json={"title": "Test Session", "language": "en-US"},
            headers=auth_headers
        )
        session_id = session_response.json()["id"]
        
        # 上傳音頻
        with open("tests/data/sample_audio.mp3", "rb") as audio_file:
            upload_response = await client.post(
                f"/api/v1/sessions/{session_id}/upload",
                files={"audio_file": audio_file},
                headers=auth_headers
            )
        
        assert upload_response.status_code == 200
        
        # 驗證 mock 被調用
        mock_gcs.assert_called_once()
        mock_stt.assert_called_once()
```

### 4. 前端組件測試

#### React 組件單元測試
```typescript
// apps/web/components/__tests__/AudioUploader.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AudioUploader } from '../AudioUploader';

describe('AudioUploader', () => {
  const mockOnUpload = jest.fn();
  
  beforeEach(() => {
    mockOnUpload.mockClear();
  });

  it('should render upload interface', () => {
    render(<AudioUploader onUpload={mockOnUpload} />);
    
    expect(screen.getByText('選擇音頻檔案')).toBeInTheDocument();
    expect(screen.getByTestId('file-input')).toBeInTheDocument();
  });

  it('should handle file selection', async () => {
    render(<AudioUploader onUpload={mockOnUpload} />);
    
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mp3' });
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('test.mp3')).toBeInTheDocument();
    });
  });

  it('should validate file type', async () => {
    render(<AudioUploader onUpload={mockOnUpload} />);
    
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(screen.getByText('不支援的檔案格式')).toBeInTheDocument();
    });
  });

  it('should handle upload progress', async () => {
    const mockUpload = jest.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 100))
    );
    
    render(<AudioUploader onUpload={mockUpload} />);
    
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mp3' });
    const input = screen.getByTestId('file-input') as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByTestId('upload-button'));
    
    expect(screen.getByTestId('progress-bar')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('上傳完成')).toBeInTheDocument();
    });
  });
});
```

### 5. 效能測試

#### 負載測試
```python
# tests/performance/test_api_performance.py
import asyncio
import time
import pytest
from httpx import AsyncClient

class TestAPIPerformance:
    @pytest.mark.performance
    async def test_concurrent_session_creation(self):
        """測試並發會話建立效能"""
        async def create_session(client: AsyncClient, session_id: int):
            start_time = time.time()
            response = await client.post(
                "/api/v1/sessions",
                json={"title": f"Session {session_id}", "language": "zh-TW"},
                headers=auth_headers
            )
            end_time = time.time()
            
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "session_id": session_id
            }
        
        # 建立 50 個並發請求
        async with AsyncClient() as client:
            tasks = [
                create_session(client, i) 
                for i in range(50)
            ]
            results = await asyncio.gather(*tasks)
        
        # 驗證效能指標
        success_count = sum(1 for r in results if r["status_code"] == 200)
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)
        
        assert success_count >= 48  # 96% 成功率
        assert avg_response_time < 0.5  # 平均響應時間 < 500ms
        assert max_response_time < 2.0  # 最大響應時間 < 2s
```

## 錯誤處理

### 測試失敗處理策略

#### 1. 自動重試機制
```python
# tests/utils/retry.py
import functools
import time

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # 指數退避
            return None
        return wrapper
    return decorator
```

#### 2. 測試資料清理
```python
# tests/utils/cleanup.py
import pytest

@pytest.fixture(autouse=True)
def cleanup_test_data(test_db):
    """自動清理測試資料"""
    yield
    
    # 測試完成後清理
    session = test_db()
    try:
        session.query(TranscriptSegment).delete()
        session.query(SessionRole).delete()
        session.query(Session).delete()
        session.query(User).delete()
        session.commit()
    finally:
        session.close()
```

## 測試策略

### 測試執行策略

#### 1. 本地開發
```bash
# 快速單元測試
make test-unit

# 整合測試
make test-integration

# 完整測試套件
make test-all
```

#### 2. CI/CD 管道
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Unit Tests
        run: |
          make test-unit
          make test-coverage

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - name: Run Integration Tests
        run: make test-integration

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Playwright
        run: npx playwright install
      - name: Run E2E Tests
        run: make test-e2e
```

### 測試資料管理

#### 1. 測試資料隔離
- 每個測試使用獨立的資料庫事務
- 測試完成後自動回滾
- 並行測試不互相干擾

#### 2. 測試資料一致性
- 使用工廠模式建立測試資料
- 標準化的測試資料模板
- 版本控制測試資料檔案

## 監控與報告

### 測試覆蓋率監控
```python
# pytest.ini
[tool:pytest]
addopts = 
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### 測試報告生成
- HTML 覆蓋率報告
- JUnit XML 格式報告
- 效能測試基準報告
- 失敗測試詳細日誌

---

**設計原則：**
1. **快速反饋** - 單元測試在 30 秒內完成
2. **可靠性** - 測試結果一致且可重現
3. **可維護性** - 測試代碼清晰易懂
4. **全面性** - 覆蓋所有關鍵功能路徑
5. **自動化** - 最小化手動測試需求