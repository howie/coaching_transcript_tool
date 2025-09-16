# WP1 - Ports & Factories Hardening

Last Updated: 2025-09-16 5:32 pm by ChatGPT

## 狀態
- 未開始（待指派）

## 目標
- 釐清所有 use case 所需的 repository 依賴，避免遺漏。
- 為 factories 的建立流程補上自動化測試與文件。
- 保留 Hybrid 模式下的 legacy ORM 轉接點，並加註 TODO 供後續移除。

## 主要檢查項目
- [ ] `src/coaching_assistant/infrastructure/factories.py` 無遞迴/循環依賴問題。
- [ ] Repository factory 與 use case factory 均有單元測試覆蓋。
- [ ] 測試檔（擴充 `tests/unit/infrastructure/test_factory_circular_reference.py`）涵蓋所有新 factory。
- [ ] `make lint`, `make test-unit`, `make test-integration` 皆成功。
- [ ] README/文件標記 legacy 暫時方案。

## 注意事項
- 任何新的 helper 需限制於 infrastructure 層，不可滲入 core。
- 若引用外部服務，請建立 interface 或 mock，保持單元測試純粹。
- 記得在完成後更新狀態與檢查項勾選。

## 交付物
- 經過 review 的 PR（含測試結果）。
- 本頁狀態更新與摘要。
