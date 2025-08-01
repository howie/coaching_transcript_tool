# 專案發展藍圖 (Project Roadmap)

本文件旨在提供 `coaching-transcript-tool` 專案從初期重構到未來發展的高層次策略規劃。它與 `todo.md` 互為補充，`todo.md` 專注於具體的執行任務，而本藍圖則闡述各階段的「目標」與「預期成果」。

## 總體願景 (Overall Vision)

將一個便利的命令列工具（CLI），轉型為一個強大、可靠且可商業化的 API 服務。初期核心目標是無縫整合至 Custom GPTs，賦予 AI 分析和處理教練對話逐字稿的能力，最終擴展到更多元的 AI Agent 和企業級應用場景。

---

## Phase 1: 基礎建設與重構 (Foundation & Refactoring)

**🎯 目標：** 將現有的 CLI 工具程式碼進行專業化重構，建立一個穩固、可測試、可擴展的核心函式庫，並為 API 服務化打下堅實基礎。

**🔑 主要任務 (對應 `todo.md`):**
- **程式碼模組化:** 將所有核心處理邏輯（解析、合併、取代、轉檔）從 `vtt.py` 抽離至 `src/coaching_transcript_tool/core` 模組。(`todo.md #1`)
- **建立 API 骨架:** 使用 FastAPI 建立 `/format` 端點，並確保其能呼叫重構後的核心邏輯。(`todo.md #2`)
- **導入單元測試:** 使用 `pytest` 為核心功能編寫測試案例，確保重構後的程式碼品質與行為一致性。(`todo.md #1`)
- **標準化開發環境:** 設定 `ruff`, `black` 等工具，統一程式碼風格與品質。(`todo.md #0`)

**✅ 預期成果:** 一個結構清晰、可被輕易匯入 (import) 的 Python 套件，以及一個功能雖簡單但已準備好擴展的 API 服務。

---

## Phase 2: API 服務化與 GPT 整合 (API Service & GPT Integration)

**🎯 目標：** 發布 MVP (Minimum Viable Product) 版本的 API 服務，並成功將其整合為 Custom GPT 的 Action，實現專案的核心價值。

**🔑 主要任務 (對應 `todo.md`):**
- **架構重構 (✅ 已完成):** 專案結構扁平化，提升可維護性。
- **完善 API 功能:** 實現檔案上傳、處理、暫存與回傳的完整流程。(`todo.md #2`)
- **雲端部署:** 將服務容器化 (Docker)，並建立自動化部署流程 (GitHub Actions) 到雲端平台 (如 Fly.io, Render)。(`todo.md #2`)
- **建立 Custom GPT Action:** 撰寫並提供 OpenAPI schema，在 GPT Builder 中設定 Action，並進行端對端測試。(`todo.md #4`)
- **撰寫基礎文件:** 完成 `README.md` 和 API 使用範例，讓開發者能快速上手。(`todo.md #9`)

**✅ 預期成果:** 一個公開可用的 API 端點，以及一個能透過對話呼叫此 API 來處理逐字稿的 Custom GPT。

---

## Phase 3: 商業化與生態系拓展 (Commercialization & Ecosystem Expansion)

**🎯 目標：** 為服務加入基礎的商業化機制，驗證市場潛力，並將其應用拓展到更多平台，建立初步的生態系。

**🔑 主要任務 (對應 `todo.md`):**
- **使用者認證與計費:** 導入 API Key 機制、設定使用額度限制 (Rate Limiting)，並規劃初步的計費方案。(`todo.md #3`)
- **整合其他平台:** 開發 Slack 或 Teams Bot 作為概念驗證 (PoC)，展示服務的多元整合能力。(`todo.md #6`)
- **市場推廣與回饋收集:** 建立產品介紹頁面，向目標社群 (如教練社群) 推廣，並收集使用者回饋。(`todo.md #10`)
- **監控與維運 (Observability):** 建立結構化的日誌 (Logging) 與錯誤追蹤 (Error Tracing) 機制，確保服務穩定性。(`todo.md #7`)

**✅ 預期成果:** 一個具備基本訂閱模式的 SaaS 服務，並在至少一個主流協作平台上有整合應用，同時擁有初步的用戶回饋循環。

---

## Phase 4: 企業級功能與未來展望 (Enterprise Features & Future Vision)

**🎯 目標：** 根據市場回饋，提升服務的安全性、可靠性，並加入能吸引高價值客戶的進階功能。

**🔑 主要任務 (對應 `todo.md`):**
- **進階 AI 功能:** 整合 Whisper 進行語音直接轉錄、自動標記 PCC Markers 或情緒線索等。(`todo.md #Backlog`)
- **安全性與隱私強化:** 實作原始檔案自動刪除、資料落地區域選擇等企業級功能。(`todo.md #8`)
- **多租戶與管理後台:** 為未來的管理儀表板 (Admin Dashboard) 和多租戶架構做準備。(`todo.md #Backlog`)
- **國際化 (i18n):** 支援多國語言介面與文件。(`todo.md #Backlog`)

**✅ 預期成果:** 一個功能強大、安全可靠，能滿足專業教練、顧問公司或企業內部訓練需求的專業級服務。
