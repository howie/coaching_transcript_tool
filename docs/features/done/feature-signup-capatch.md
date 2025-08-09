Signup 頁面防機器人機制規格書（Draft v0.1）

本文件說明在現有 Next.js／FastAPI 架構中，於使用者註冊（Signup）流程導入 Google reCAPTCHA v3 或 Invisible reCAPTCHA 的完整規格，確保可阻擋自動化機器人（Bot）濫用，同時維持良好使用者體驗。

⸻

1．目標與範圍
	1.	首要目標：防範惡意 Bot 批量註冊、撞庫、暴力測試等行為。
	2.	範圍：僅限「/signup」頁面（含 API /api/auth/signup）之人機驗證；未涵蓋登入、忘記密碼、第三方 OAuth 等其他入口。
	3.	期望使用者體驗：
	•	優先採用 Invisible reCAPTCHA 或 reCAPTCHA v3（無互動式 Challenge），盡量降低人為點擊、輸入負擔。
	•	當 Google 服務被封鎖或故障時，自動降級至 fallback（例如 hCaptcha、傳統 reCAPTCHA v2 Checkbox 或簡易圖形驗證）。

⸻

2．技術選型

機制	優點	缺點	備註
Google reCAPTCHA v3	無須使用者互動；提供 0–1 分數，可依風險動態判斷	需要後端二次驗證；分數判斷需自行設閾值	推薦閾值 0.5–0.7；低於閾值可觸發二次驗證或封鎖
Invisible reCAPTCHA v2	幾乎零 UI；在可疑時才彈出圖片 Challenge	實做稍複雜；仍可能出現彈窗打斷 UX	可做為 v3 的降級方案
hCaptcha	無 Google 依賴；GDPR 友善	需額外整合；品牌認知度低	首選服務失效時作為 fallback


⸻

3．流程說明

graph TD
  subgraph Frontend (Next.js)
    A[使用者填寫 Signup 表單] --> B[呼叫 reCAPTCHA JS SDK]
    B --> C[取得 token]
    C --> D[POST /api/auth/signup + token]
  end
  subgraph Backend (FastAPI)
    D --> E[驗證表單資料]
    E --> F[POST https://www.google.com/recaptcha/api/siteverify]
    F --> G{score ≥ threshold?}
    G -- Yes --> H[建立帳號]
    G -- No --> I[記錄 & 阻擋｜回傳 403]
  end

3.1 前端
	1.	以 next-recaptcha-v3（或自行載入 https://www.google.com/recaptcha/api.js?render=SITE_KEY）取得 token。
	2.	在表單提交前呼叫 grecaptcha.execute(SITE_KEY, {action: 'signup'})。
	3.	取得 token 後於 fetch body 中攜帶：

{
  "email": "user@example.com",
  "password": "***",
  "recaptchaToken": "<token>"
}


	4.	若前端偵測到 window.grecaptcha === undefined（被阻擋）→ fallback 案例：顯示 hCaptcha（或 v2 Checkbox）元件。

3.2 後端
	1.	以 環境變數 管理：
	•	RECAPTCHA_SECRET（Server Secret）
	•	RECAPTCHA_MIN_SCORE（預設 0.6）
	2.	FastAPI 端點 POST /api/auth/signup 伺服器邏輯：

async def verify_recaptcha(token: str, remote_ip: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET,
                "response": token,
                "remoteip": remote_ip,
            }, timeout=5
        )
    data = resp.json()
    return data.get("success"), data.get("score", 0), data.get("action")


	3.	檢查 action == 'signup'；score >= RECAPTCHA_MIN_SCORE 才放行。
	4.	低分或失敗時：
	•	回傳 HTTP 403，訊息 {"detail": "Failed Human Verification"}。
	•	記錄 log、增加 IP ／ Email 風險分數、可加入 Redis 限速。
	5.	系統監控：統計每日 token 請求量、平均 score、阻擋率，輸出至 Grafana Dashboard。

⸻

4．UI／UX 規範
	1.	Signup 按鈕需 disabled 狀態，直到 reCAPTCHA token 取得與表單欄位通過基本驗證。
	2.	錯誤提示須於表單內 Inline 顯示，避免重整。
	3.	Accessibility：Invisible reCAPTCHA 已符合 WCAG，仍須保留語意化按鈕標籤與 aria-live 錯誤訊息。
	4.	Fallback 人機驗證須支援鍵盤操作與螢幕閱讀（reCAPTCHA v2 有語音選項）。

⸻

5．安全與隱私考量
	1.	僅於後端儲存 success/score/action, user_ip, user_agent，保留 30 天；避免紀錄完整 token 或個資。
	2.	GDPR：需於隱私權政策更新「使用 Google reCAPTCHA 服務；其收集 Cookie 與使用者裝置資訊」之條款。
	3.	使用 HTTPS；避免中間人竄改 token。
	4.	後端驗證 timeout 設 5 秒並重試 1 次；連續失敗超過閾值時暫時關閉註冊，通知運維人員。

⸻

6．部署 & 環境變數

環境	變數	說明
local	RECAPTCHA_SITE_KEY_LOCAL / SECRET_LOCAL	本機測試（可用測試 Key 或 Stub）
staging	RECAPTCHA_SITE_KEY_STG / SECRET_STG	與 Google Console Staging 網域對應
production	RECAPTCHA_SITE_KEY / RECAPTCHA_SECRET	僅限正式網域，並限制來源 IP


⸻

7．測試策略
	1.	單元測試：使用 pytest／pytest-asyncio 模擬 Google API 回傳各種分數、錯誤碼。
	2.	E2E 測試：Cypress or Playwright 模擬使用者註冊流程；Mock Google JS；檢查 token 有傳至後端。
	3.	Rate-Limit 測試：JMeter or k6 模擬高頻註冊；確保 reCAPTCHA 阻擋率 ≥ 90 %。
	4.	Accessibility 測試：Lighthouse Audit AA，確保無低對比文字或缺乏 ARIA。

⸻

8．驗收準則（Checklist）
	•	reCAPTCHA v3 token 在「正常流量」下成功率 ≥ 95%。
	•	雙重驗證（分數 < 閾值）時自動切換 Invisible reCAPTCHA，成功率 ≥ 98%。
	•	當 Google API 故障，系統自動顯示 fallback 圖形驗證。
	•	每日阻擋統計寫入 Prometheus，Grafana 儀表板可視化。
	•	DevSecOps Pipeline 自動執行單元／E2E 測試，通過率 100%。

⸻

本規格完成後，請建立對應 PR（包含環境變數、前後端程式碼、CI 測試腳本）並附帶 Screencast 示範 Invisible reCAPTCHA 及 fallback 情境。