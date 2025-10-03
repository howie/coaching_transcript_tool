# Cloudflare Pages 自動部署設定指南

## 問題描述
Cloudflare Pages 自動部署失敗，錯誤訊息：
```
✘ [ERROR] The entry-point file at ".open-next/worker.js" was not found.
```

## 根本原因
1. Cloudflare Pages 未正確執行 Next.js + OpenNext 的構建流程
2. Monorepo 結構需要指定正確的根目錄 (`apps/web`)
3. 需要兩步構建：`npm run build` → `npm run build:cf`

---

## 解決方案：Cloudflare Dashboard 設定

### 步驟 1：登入 Cloudflare Dashboard

1. 前往 https://dash.cloudflare.com
2. 選擇您的帳戶
3. 點選 **Pages** → 找到 `coachly-doxa-com-tw` 專案

### 步驟 2：設定構建配置

進入 **Settings** → **Builds & deployments** → **Build configurations**

設定以下參數：

| 設定項目 | 值 | 說明 |
|---------|---|------|
| **Framework preset** | `Next.js (Static HTML Export)` 或 `None` | 選擇框架預設 |
| **Build command** | `npm run build && npm run build:cf` | 兩步構建流程 |
| **Build output directory** | `.open-next` | OpenNext 輸出目錄 |
| **Root directory (advanced)** | `apps/web` | Monorepo 子目錄 |

### 步驟 3：設定環境變數

在 **Settings** → **Environment variables** 新增：

**Production 環境**：
```
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.doxa.com.tw
```

**Preview 環境**（可選）：
```
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api-staging.doxa.com.tw
```

### 步驟 4：重新部署

1. 回到 **Deployments** 頁面
2. 點選最新的失敗部署
3. 點選 **Retry deployment** 按鈕

---

## 驗證構建成功

構建成功的標誌：
```
✅ Uploading...
✅ Deployment complete!
```

構建過程應該會顯示：
```
> npm run build
> npm run build:cf
✓ Compiled successfully
✓ OpenNext build completed
```

---

## Node.js 版本控制

專案已建立 `apps/web/.nvmrc` 檔案，指定 Node.js 版本為 `20`。

Cloudflare Pages 會自動讀取此檔案並使用對應版本。

---

## 常見問題

### Q1: 構建時找不到 `npm` 指令
**A**: 確認 Root directory 設定為 `apps/web`，且 `package.json` 存在於該目錄。

### Q2: 環境變數沒有生效
**A**: `NEXT_PUBLIC_*` 變數需要在**構建時**注入，請確認在 Environment variables 中設定，並重新觸發構建。

### Q3: 構建成功但頁面顯示錯誤
**A**: 檢查 `wrangler.toml` 中的 `[vars]` 區塊，確認 runtime 環境變數正確。

---

## 本地部署 vs 自動部署

| 方式 | 指令 | 用途 |
|------|------|------|
| **本地部署** | `make deploy-frontend` | 開發者手動部署到 Cloudflare |
| **自動部署** | Git push → Cloudflare Pages | CI/CD 自動化部署 |

兩種方式設定完成後可以並存使用。

---

## 參考資料

- [Cloudflare Pages - Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)
- [OpenNext Cloudflare Adapter](https://github.com/opennextjs/opennextjs-cloudflare)
- [Next.js Environment Variables](https://nextjs.org/docs/app/building-your-application/configuring/environment-variables)
