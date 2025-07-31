# 重構計劃：前後端分離 + 混合部署策略

**計劃版本：** v1.0  
**制定日期：** 2025-07-31  
**預計完成：** 2025-09-30 (10週)  
**架構選擇：** 方案 2 - 混合部署策略

## 🎯 目標架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js       │    │  CF Workers      │    │   FastAPI       │
│ (CF Pages)      │ -> │  (API Gateway)   │ -> │ (GCP Cloud Run) │
│ - SSR/SSG       │    │ - 認證中間件      │    │ - 核心業務邏輯   │
│ - 響應式 UI     │    │ - Rate Limiting  │    │ - 檔案處理      │
│ - NextAuth      │    │ - 快取層        │    │ - 資料庫存取    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 現況分析

### 當前問題
- [x] Flask + FastAPI 混合架構複雜
- [x] 前端模板與 API 耦合度高
- [x] 認證系統不完整
- [x] 靜態檔案管理分散
- [x] 部署配置複雜

### 目標成果
- [ ] 清晰的前後端分離
- [ ] 全球化的邊緣運算優勢
- [ ] 現代化的開發體驗
- [ ] 可擴展的企業級架構
- [ ] 成本最佳化的部署策略

---

## 🚀 實作階段

### **階段 1：基礎架構準備** (Week 1-2)

#### 1.1 專案結構重組

**新的目錄結構：**
```
coaching_transcript_tool/
├── README.md                           # 更新主要說明
├── package.json                        # Monorepo 根配置
├── turbo.json                          # Turborepo 配置
├── .env.example                        # 環境變數範例
├── 
├── apps/
│   ├── frontend/                       # Next.js 應用
│   │   ├── app/                        # App Router
│   │   │   ├── (dashboard)/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── transcript-converter/
│   │   │   │   └── layout.tsx
│   │   │   ├── auth/
│   │   │   ├── api/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/                 # 可重用組件
│   │   │   ├── ui/                     # 基礎 UI 組件
│   │   │   ├── forms/                  # 表單組件
│   │   │   └── layout/                 # 佈局組件
│   │   ├── lib/                        # 工具函式
│   │   │   ├── auth.ts                 # NextAuth 配置
│   │   │   ├── api.ts                  # API 客戶端
│   │   │   └── utils.ts                # 通用工具
│   │   ├── public/                     # 靜態資源
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   └── tsconfig.json
│   │
│   ├── gateway/                        # CF Workers API Gateway
│   │   ├── src/
│   │   │   ├── index.ts                # 主要入口
│   │   │   ├── middleware/             # 中間件
│   │   │   │   ├── auth.ts             # 認證中間件
│   │   │   │   ├── cors.ts             # CORS 處理
│   │   │   │   ├── rate-limit.ts       # 流量限制
│   │   │   │   └── cache.ts            # 快取層
│   │   │   ├── routes/                 # 路由處理
│   │   │   │   ├── health.ts
│   │   │   │   ├── format.ts
│   │   │   │   └── user.ts
│   │   │   └── utils/                  # 工具函式
│   │   ├── wrangler.toml               # CF Workers 配置
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── backend/                        # FastAPI 應用 (重構現有)
│       ├── src/
│       │   └── coaching_assistant/     # 保持現有結構
│       │       ├── __init__.py
│       │       ├── main.py             # FastAPI 主應用
│       │       ├── api/                # API 路由
│       │       │   ├── __init__.py
│       │       │   ├── health.py
│       │       │   ├── format.py
│       │       │   └── user.py
│       │       ├── core/               # 現有核心邏輯
│       │       ├── middleware/         # 中間件
│       │       │   ├── __init__.py
│       │       │   ├── cors.py
│       │       │   ├── logging.py
│       │       │   └── error_handler.py
│       │       ├── models/             # 資料模型
│       │       │   ├── __init__.py
│       │       │   ├── user.py
│       │       │   └── transcript.py
│       │       ├── services/           # 業務邏輯服務
│       │       │   ├── __init__.py
│       │       │   ├── auth_service.py
│       │       │   └── transcript_service.py
│       │       └── utils/              # 現有工具函式
│       ├── requirements.txt
│       ├── Dockerfile
│       └── cloudbuild.yaml             # GCP 部署配置
│
├── packages/                           # 共用套件
│   ├── shared-types/                   # TypeScript 型別定義
│   │   ├── src/
│   │   │   ├── api.ts                  # API 型別
│   │   │   ├── user.ts                 # 用戶型別
│   │   │   └── transcript.ts           # 逐字稿型別
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── eslint-config/                  # 共用 ESLint 配置
│       ├── index.js
│       └── package.json
│
├── docs/                               # 現有文件
└── scripts/                            # 部署腳本
    ├── deploy-frontend.sh
    ├── deploy-gateway.sh
    └── deploy-backend.sh
```

#### 1.2 技術棧選擇

**前端技術棧：**
```json
{
  "framework": "Next.js 14",
  "language": "TypeScript",
  "styling": "Tailwind CSS + shadcn/ui",
  "auth": "NextAuth.js v4",
  "forms": "React Hook Form + Zod",
  "state": "Zustand (輕量級狀態管理)",
  "testing": "Jest + Testing Library",
  "deployment": "Cloudflare Pages"
}
```

**Gateway 技術棧：**
```json
{
  "runtime": "Cloudflare Workers",
  "framework": "Hono.js",
  "language": "TypeScript",
  "validation": "Zod",
  "cache": "CF Cache API",
  "auth": "JWT + Google OAuth",
  "deployment": "Wrangler CLI"
}
```

**後端技術棧：**
```json
{
  "framework": "FastAPI (現有)",
  "language": "Python 3.10+",
  "database": "GCP Cloud SQL (PostgreSQL)",
  "auth": "Google Identity Platform",
  "storage": "GCP Cloud Storage",
  "monitoring": "GCP Operations Suite",
  "deployment": "GCP Cloud Run"
}
```

#### 1.3 開發環境設定

**根目錄 package.json：**
```json
{
  "name": "coaching-transcript-tool",
  "private": true,
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "deploy:frontend": "./scripts/deploy-frontend.sh",
    "deploy:gateway": "./scripts/deploy-gateway.sh",
    "deploy:backend": "./scripts/deploy-backend.sh",
    "deploy:all": "npm run deploy:backend && npm run deploy:gateway && npm run deploy:frontend"
  },
  "devDependencies": {
    "turbo": "^1.10.0",
    "@changesets/cli": "^2.26.0"
  }
}
```

---

### **階段 2：前端重構** (Week 3-4)

#### 2.1 Next.js 應用建立

**App Router 結構：**
```typescript
// app/layout.tsx
import { Inter } from 'next/font/google'
import { Providers } from '@/components/providers'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}

// app/page.tsx - Landing Page
import { HeroSection } from '@/components/sections/hero'
import { FeatureSection } from '@/components/sections/features'
import { PricingSection } from '@/components/sections/pricing'

export default function HomePage() {
  return (
    <main>
      <HeroSection />
      <FeatureSection />
      <PricingSection />
    </main>
  )
}

// app/(dashboard)/layout.tsx
import { DashboardHeader } from '@/components/layout/dashboard-header'
import { DashboardSidebar } from '@/components/layout/dashboard-sidebar'
import { getServerSession } from 'next-auth/next'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession()
  
  if (!session) {
    redirect('/auth/signin')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader />
      <div className="flex">
        <DashboardSidebar />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
```

#### 2.2 認證系統實作

**NextAuth.js 配置：**
```typescript
// lib/auth.ts
import { NextAuthOptions } from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import { JWT } from 'next-auth/jwt'

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        token.accessToken = account.access_token
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string
      return session
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
}

// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth'
import { authOptions } from '@/lib/auth'

const handler = NextAuth(authOptions)
export { handler as GET, handler as POST }
```

#### 2.3 API 客戶端

**API 客戶端配置：**
```typescript
// lib/api.ts
import { getSession } from 'next-auth/react'

class ApiClient {
  private baseUrl: string
  
  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://gateway.yourdomain.com'
  }

  private async getHeaders() {
    const session = await getSession()
    return {
      'Content-Type': 'application/json',
      ...(session?.accessToken && {
        'Authorization': `Bearer ${session.accessToken}`
      })
    }
  }

  async uploadTranscript(file: File, options: TranscriptOptions) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('options', JSON.stringify(options))

    const response = await fetch(`${this.baseUrl}/api/v1/format`, {
      method: 'POST',
      headers: await this.getHeaders(),
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.blob()
  }
}

export const apiClient = new ApiClient()
```

---

### **階段 3：API Gateway 開發** (Week 5-6)

#### 3.1 CF Workers Gateway 基礎架構

**主要入口檔案：**
```typescript
// gateway/src/index.ts
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { logger } from 'hono/logger'
import { authMiddleware } from './middleware/auth'
import { rateLimitMiddleware } from './middleware/rate-limit'
import { cacheMiddleware } from './middleware/cache'
import { errorHandler } from './middleware/error-handler'

// 路由導入
import healthRoutes from './routes/health'
import formatRoutes from './routes/format'
import userRoutes from './routes/user'

const app = new Hono<{
  Bindings: {
    BACKEND_URL: string
    JWT_SECRET: string
    RATE_LIMIT_KV: KVNamespace
    CACHE_KV: KVNamespace
  }
}>()

// 全域中間件
app.use('*', logger())
app.use('*', cors({
  origin: ['https://yourdomain.com', 'http://localhost:3000'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
}))
app.use('*', errorHandler)

// 公開路由
app.route('/health', healthRoutes)

// 需要認證的路由
app.use('/api/*', authMiddleware)
app.use('/api/*', rateLimitMiddleware)
app.use('/api/v1/format', cacheMiddleware)

app.route('/api/v1', formatRoutes)
app.route('/api/v1/user', userRoutes)

export default app
```

#### 3.2 認證中間件

```typescript
// gateway/src/middleware/auth.ts
import { createMiddleware } from 'hono/factory'
import { verify } from 'hono/jwt'

export const authMiddleware = createMiddleware(async (c, next) => {
  const token = c.req.header('Authorization')?.replace('Bearer ', '')
  
  if (!token) {
    return c.json({ error: 'Unauthorized' }, 401)
  }

  try {
    const payload = await verify(token, c.env.JWT_SECRET)
    c.set('user', payload)
    await next()
  } catch (error) {
    return c.json({ error: 'Invalid token' }, 401)
  }
})
```

#### 3.3 Rate Limiting 中間件

```typescript
// gateway/src/middleware/rate-limit.ts
import { createMiddleware } from 'hono/factory'

export const rateLimitMiddleware = createMiddleware(async (c, next) => {
  const ip = c.req.header('CF-Connecting-IP') || 'unknown'
  const user = c.get('user')
  const key = user ? `user:${user.sub}` : `ip:${ip}`
  
  const now = Date.now()
  const windowMs = 60 * 1000 // 1 minute
  const maxRequests = user ? 100 : 20 // 認證用戶更高限制

  const current = await c.env.RATE_LIMIT_KV.get(key)
  const data = current ? JSON.parse(current) : { count: 0, resetTime: now + windowMs }

  if (now > data.resetTime) {
    data.count = 0
    data.resetTime = now + windowMs
  }

  if (data.count >= maxRequests) {
    return c.json({
      error: 'Rate limit exceeded',
      resetTime: data.resetTime
    }, 429)
  }

  data.count++
  await c.env.RATE_LIMIT_KV.put(key, JSON.stringify(data), {
    expirationTtl: Math.ceil(windowMs / 1000)
  })

  await next()
})
```

#### 3.4 快取中間件

```typescript
// gateway/src/middleware/cache.ts
import { createMiddleware } from 'hono/factory'
import { createHash } from 'crypto'

export const cacheMiddleware = createMiddleware(async (c, next) => {
  if (c.req.method !== 'POST') {
    await next()
    return
  }

  // 為檔案上傳請求創建快取鍵
  const body = await c.req.formData()
  const file = body.get('file') as File
  const options = body.get('options') as string

  if (!file) {
    await next()
    return
  }

  const fileHash = createHash('sha256')
    .update(await file.arrayBuffer())
    .digest('hex')
  
  const cacheKey = `format:${fileHash}:${options}`
  
  // 檢查快取
  const cached = await c.env.CACHE_KV.get(cacheKey)
  
  if (cached) {
    const response = new Response(cached, {
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'X-Cache': 'HIT'
      }
    })
    return response
  }

  await next()
  
  // 快取響應
  if (c.res.status === 200) {
    const responseClone = c.res.clone()
    const responseBody = await responseClone.arrayBuffer()
    
    await c.env.CACHE_KV.put(cacheKey, responseBody, {
      expirationTtl: 3600 // 1 hour cache
    })
    
    c.res.headers.set('X-Cache', 'MISS')
  }
})
```

#### 3.5 路由處理

**檔案處理路由：**
```typescript
// gateway/src/routes/format.ts
import { Hono } from 'hono'

const app = new Hono<{
  Bindings: {
    BACKEND_URL: string
  }
}>()

app.post('/format', async (c) => {
  const formData = await c.req.formData()
  const user = c.get('user')

  // 轉發到後端 FastAPI
  const backendResponse = await fetch(`${c.env.BACKEND_URL}/api/v1/format`, {
    method: 'POST',
    headers: {
      'X-User-ID': user.sub,
      'X-User-Email': user.email,
    },
    body: formData,
  })

  if (!backendResponse.ok) {
    return c.json({
      error: 'Backend processing failed',
      details: await backendResponse.text()
    }, backendResponse.status)
  }

  // 回傳處理結果
  const result = await backendResponse.blob()
  return new Response(result, {
    headers: {
      'Content-Type': backendResponse.headers.get('Content-Type') || 'application/octet-stream',
      'Content-Disposition': backendResponse.headers.get('Content-Disposition') || 'attachment'
    }
  })
})

export default app
```

---

### **階段 4：後端重構與部署** (Week 7-8)

#### 4.1 FastAPI 應用重構

**主應用入口：**
```python
# apps/backend/src/coaching_assistant/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging
import os

from .api import health, format_routes, user
from .middleware.logging import setup_logging
from .middleware.error_handler import error_handler
from .core.config import settings

# 設定日誌
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Coaching Transcript Tool API",
    description="Backend API for processing coaching transcripts",
    version="2.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# 中間件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 錯誤處理
app.add_exception_handler(Exception, error_handler)

# 路由
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(format_routes.router, prefix="/api/v1", tags=["format"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Coaching Transcript Tool Backend API v2.0.0")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Coaching Transcript Tool Backend API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "coaching_assistant.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=settings.DEBUG,
        log_level="info"
    )
```

**設定管理：**
```python
# apps/backend/src/coaching_assistant/core/config.py
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # 基本設定
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-secret-key"
    
    # API 設定
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # 資料庫設定
    DATABASE_URL: str = ""
    
    # Google Cloud 設定
    GOOGLE_PROJECT_ID: str = ""
    GOOGLE_STORAGE_BUCKET: str = ""
    
    # 認證設定
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # 監控設定
    SENTRY_DSN: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

#### 4.2 資料模型

**用戶模型：**
```python
# apps/backend/src/coaching_assistant/models/user.py
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String)
    provider = Column(String, default="google")
    provider_id = Column(String, unique=True, index=True)
    
    # 訂閱資訊
    subscription_tier = Column(String, default="free")
    usage_count = Column(Integer, default=0)
    usage_limit = Column(Integer, default=10)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

**逐字稿記錄模型：**
```python
# apps/backend/src/coaching_assistant/models/transcript.py
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .user import Base

class TranscriptRecord(Base):
    __tablename__ = "transcript_records"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 檔案資訊
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer)
    file_hash = Column(String, index=True)
    
    # 處理參數
    output_format = Column(String, nullable=False)
    coach_name = Column(String)
    client_name = Column(String)
    convert_to_traditional = Column(Boolean, default=False)
    
    # 處理結果
    status = Column(String, default="processing")  # processing, completed, failed
    processing_time = Column(Integer)  # 毫秒
    error_message = Column(Text)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # 關聯
    user = relationship("User", back_populates="transcript_records")
```

#### 4.3 GCP 部署配置

**Cloud Run 部署配置：**
```yaml
# apps/backend/cloudbuild.yaml
steps:
  # 建置 Docker 映像
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', 'gcr.io/$PROJECT_ID/coaching-transcript-api:$COMMIT_SHA',
      '-t', 'gcr.io/$PROJECT_ID/coaching-transcript-api:latest',
      '-f', 'apps/backend/Dockerfile',
      '.'
    ]

  # 推送映像到 Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/coaching-transcript-api:$COMMIT_SHA']

  # 部署到 Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args: [
      'run', 'deploy', 'coaching-transcript-api',
      '--image', 'gcr.io/$PROJECT_ID/coaching-transcript-api:$COMMIT_SHA',
      '--region', 'asia-east1',
      '--platform', 'managed',
      '--allow-unauthenticated',
      '--set-env-vars', 'ENVIRONMENT=production',
      '--memory', '2Gi',
      '--cpu', '2',
      '--max-instances', '100',
      '--concurrency', '80'
    ]

images:
  - 'gcr.io/$PROJECT_ID/coaching-transcript-api:$COMMIT_SHA'
  - 'gcr.io/$PROJECT_ID/coaching-transcript-api:latest'
```

**更新的 Dockerfile：**
```dockerfile
# apps/backend/Dockerfile
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY apps/backend/requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY apps/backend/src/ ./src/

# 建立非 root 用戶
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 設定環境變數
ENV PYTHONPATH=/app/src
ENV PORT=8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# 啟動應用
CMD ["python", "-m", "uvicorn", "coaching_assistant.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### **階段 5：整合測試與優化** (Week 9-10)

#### 5.1 端對端測試

**前端測試：**
```typescript
// apps/frontend/__tests__/transcript-converter.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TranscriptConverter } from '@/app/(dashboard)/transcript-converter/page'

describe('Transcript Converter', () => {
  it('should upload and process file successfully', async () => {
    render(<TranscriptConverter />)
    
    const fileInput = screen.getByLabelText(/upload file/i)
    const file = new File(['test content'], 'test.vtt', { type: 'text/vtt' })
    
    fireEvent.change(fileInput, { target: { files: [file] } })
    
    const submitButton = screen.getByRole('button', { name: /convert/i })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/processing/i)).toBeInTheDocument()
    })
  })
})
```

**API 整合測試：**
```python
# apps/backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from coaching_assistant.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_format_transcript():
    with open("tests/data/sample.vtt", "rb") as f:
        response = client.post(
            "/api/v1/format",
            files={"file": ("sample.vtt", f, "text/vtt")},
            data={"output_format": "excel"}
        )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
```

#### 5.2 效能優化

**Gateway 效能監控：**
```typescript
// gateway/src/middleware/performance.ts
import { createMiddleware } from 'hono/factory'

export const performanceMiddleware = createMiddleware(async (c, next) => {
  const start = Date.now()
  
  await next()
  
  const duration = Date.now() - start
  
  // 記錄效能指標
  c.res.headers.set('X-Response-Time', `${duration}ms`)
  
  // 發送到分析服務
  if (duration > 1000) {
    console.warn(`Slow request: ${c.req.path} took ${duration}ms`)
  }
})
```

#### 5.3 監控與警報

**Sentry 錯誤追蹤：**
```typescript
// apps/frontend/lib/sentry.ts
import * as Sentry from '@sentry/nextjs'

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
})
```

```python
# apps/backend/src/coaching_assistant/middleware/sentry.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

def setup_sentry():
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[
            FastApiIntegration(auto_enabling_integrations=False),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=1.0,
    )
```

---

## 📋 實作檢查清單

### **階段 1 檢查清單** ✅
- [ ] 建立 Monorepo 結構
- [ ] 設定 Turborepo 配置
- [ ] 建立共用型別定義
- [ ] 設定開發環境工具
- [ ] 更新 README 和文件

### **階段 2 檢查清單** ✅
- [ ] Next.js 14 應用建立
- [ ] App Router 結構實作
- [ ] NextAuth.js 認證設定
- [ ] 響應式 UI 組件開發
- [ ] API 客戶端實作
- [ ] 前端測試撰寫

### **階段 3 檢查清單** ✅
- [ ] CF Workers Gateway 建立
- [ ] Hono.js 路由設定
- [ ] 認證中間件實作
- [ ] Rate Limiting 機制
- [ ] 快取層實作
- [ ] 錯誤處理中間件

### **階段 4 檢查清單** ✅
- [ ] FastAPI 應用重構
- [ ] 資料庫模型設計
- [ ] GCP Cloud Run 配置
- [ ] CI/CD Pipeline 設定
- [ ] 環境變數管理
- [ ] 健康檢查端點

### **階段 5 檢查清單** ✅
- [ ] 端對端測試撰寫
- [ ] 效能基準測試
- [ ] 監控系統設定
- [ ] 錯誤追蹤配置
- [ ] 安全性測試
- [ ] 上線前檢查

---

## 🚀 部署策略

### **開發環境：**
```bash
# 啟動所有服務
npm run dev

# 前端: http://localhost:3000
# Gateway: http://localhost:8787 (wrangler dev)
# Backend: http://localhost:8000
```

### **測試環境：**
```bash
# 部署到測試環境
npm run deploy:all -- --env=staging
```

### **生產環境：**
```bash
# 部署到生產環境
npm run deploy:all -- --env=production
```

---

## 💰 成本估算

### **月費用預估（中等使用量）：**
- **Cloudflare Workers:** $5-20 (100K requests)
- **Cloudflare Pages:** $0-20 (Unlimited static hosting)
- **GCP Cloud Run:** $20-50 (CPU time based)
- **GCP Cloud SQL:** $25-50 (db-f1-micro instance)
- **GCP Cloud Storage:** $1-5 (1GB storage)

**總計:** $51-145/月

### **節省成本策略：**
1. **智能快取：** CF Workers 快取減少後端呼叫
2. **請求過濾：** Gateway 層過濾無效請求
3. **按需擴展：** Cloud Run 零請求時不收費
4. **資源優化：** 適當的 CPU/Memory 配置

---

## 🔒 安全性考量

### **認證與授權：**
- JWT Token 驗證
- Google OAuth 2.0 整合
- API Key 管理
- 角色權限控制

### **資料保護：**
- HTTPS 全程加密
- 檔案自動清理
- 敏感資料遮蔽
- GDPR 合規

### **API 安全：**
- Rate Limiting
- CORS 設定
- Input 驗證
- SQL Injection 防護

---

## 📈 監控指標

### **關鍵指標 (KPIs)：**
- **回應時間:** < 2秒 (95th percentile)
- **可用性:** > 99.5%
- **錯誤率:** < 1%
- **使用者滿意度:** > 4.5/5

### **業務指標：**
- 每日活躍用戶 (DAU)
- 檔案處理成功率
- 轉換率 (免費 → 付費)
- 客戶支援工單數量

---

## 🔮 未來擴展計劃

### **短期 (6個月)：**
- Whisper API 整合
- 多語言支援
- 批次處理功能
- Mobile App 開發

### **中期 (12個月)：**
- AI 分析功能
- 自動標記系統
- 企業版功能
- 多租戶架構

### **長期 (24個月)：**
- 全球多區域部署
- 進階 AI 功能
- 合作夥伴 API
- 白標解決方案

---

*本重構計劃將幫助您建立一個現代化、可擴展且具成本效益的 SaaS 架構。如有任何問題或需要調整，請隨時討論。*
