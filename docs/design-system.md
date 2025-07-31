# Coachly 設計系統

## 🎨 設計理念

Coachly 採用**情境式雙主題設計系統**，根據不同使用場景提供最適合的視覺體驗：

- **Landing Page**: 清新友好的行銷風格，吸引潛在用戶
- **Dashboard**: 專業沉穩的應用風格，專注工作效率

## 🌊 Landing Page 主題

### 色彩系統

```css
:root {
  /* 主色調 - 天藍色系 */
  --primary-blue: #71c9f1;
  --primary-blue-rgb: 113, 201, 241;
  
  /* 導航背景 */
  --nav-background: #2c3e50;
  
  /* 強調色 - 更新為藍色系統一 */
  --accent-primary: #71c9f1;
  --accent-primary-hover: #60a5fa;
  --accent-orange: #ff6b35; /* 保留橙色註冊按鈕 */
  --accent-orange-hover: #e55a2b;
  
  /* 背景色 */
  --hero-background: #71c9f1;
  --section-light: #f8f9fa;
  --section-dark: #71c9f1;
  --footer-background: #2c3e50; /* 更新 Footer 背景 */
  
  /* 文字色 */
  --text-primary: #000000;
  --text-secondary: #6c757d;
  --text-on-blue: #ffffff;
  --text-on-blue-secondary: rgba(255, 255, 255, 0.8);
  
  /* 其他 */
  --white: #ffffff;
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  --border-radius: 8px;
  --transition: all 0.3s ease;
}
```

### 導航設計
- **背景**: `#2c3e50` (深藍色)
- **Logo 顏色**: 白色，hover 時變為 `#71c9f1`
- **導航項目**: 白色文字，hover 時變為 `#71c9f1`
- **主按鈕**: `#ff6b35` 背景，白色文字
- **高度**: 64px
- **陰影**: `0 2px 10px rgba(0,0,0,0.1)`

### Hero Section
- **背景**: `#71c9f1` (天藍色)
- **文字**: 白色
- **標題**: 48px, 700 字重
- **副標題**: 20px, 半透明白色
- **主按鈕**: 白色背景，深藍色文字 `#1C2E4A`
- **次按鈕**: 透明背景，白色邊框

### 內容區段
- **淺色區段**: `#f8f9fa` 背景
- **深色區段**: `#71c9f1` 背景
- **卡片**: 白色背景，圓角 8px，陰影效果
- **圖標**: `#71c9f1` 色彩

## 🏢 Dashboard 主題

### 色彩系統

```css
:root {
  /* 主背景 - 深藍色系 */
  --primary-bg: #1C2E4A;
  
  /* Header 和 Sidebar - 淺藍色系 */
  --header-sidebar-bg: #71c9f1;
  
  /* 強調色 - 黃色系 */
  --accent-color: #F5C451;
  --accent-hover: #f3c043;
  --accent-rgba: rgba(245, 196, 81, 0.1);
  --accent-border: rgba(245, 196, 81, 0.3);
  
  /* 統計數字 - 淺藍色系 */
  --stats-color: #71c9f1;
  
  /* 文字色 */
  --text-primary: #ffffff;
  --text-secondary: #b0bdc8;
  --text-tertiary: #94a3b8;
  --text-on-light-blue: #ffffff; /* 淺藍色背景上的文字 */
  
  /* 介面元素 */
  --sidebar-width: 250px;
  --header-height: 60px;
  --card-bg: rgba(255, 255, 255, 0.05);
  --card-border: rgba(245, 196, 81, 0.1);
  --input-bg: rgba(255, 255, 255, 0.05);
  
  /* 陰影與效果 */
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  --border-radius: 8px;
  --transition: all 0.3s ease;
}
```

### 頂部導航
- **背景**: `#1C2E4A`
- **高度**: 60px
- **邊框**: 底部有淡黃色邊框 `rgba(245, 196, 81, 0.2)`
- **Logo**: 產品名稱為白色 `#ffffff`
- **用戶資訊**: 灰色 `#b0bdc8`
- **登出按鈕**: 黃色邊框，hover 時黃色背景

### 側邊欄
- **背景**: `#1C2E4A`
- **寬度**: 250px (摺疊時 60px)
- **選單項目**: 
  - 預設: 灰色 `#b0bdc8`
  - 活躍/hover: 黃色 `#F5C451`，淡黃色背景
  - 左邊框線: 黃色強調

### 主內容區
- **背景**: `#1C2E4A`
- **標題**: 黃色 `#F5C451`，32px
- **副標題**: 灰色 `#94a3b8`
- **卡片**: 半透明背景，淡黃色邊框

### 統計卡片
- **背景**: 卡片背景
- **數字**: 黃色 `#F5C451`，32px，700 字重
- **標籤**: 灰色 `#94a3b8`

### 按鈕設計
- **主按鈕**: 黃色背景 `#F5C451`，深藍色文字
- **次按鈕**: 灰色背景 `#334155`，灰色文字
- **禁用按鈕**: 更深灰色，cursor: not-allowed

### 表單元素
- **輸入框**: 
  - 背景: `rgba(255, 255, 255, 0.05)`
  - 邊框: `rgba(245, 196, 81, 0.3)`
  - focus: 黃色邊框
  - placeholder: 灰色 `#b0bdc8`

## 📝 轉換器頁面特殊樣式

### 上傳區域
- **邊框**: 虛線邊框 `rgba(245, 196, 81, 0.3)`
- **hover/dragover**: 黃色邊框，淡黃色背景
- **圖標**: 黃色 `#F5C451`，48px
- **背景**: `rgba(255, 255, 255, 0.02)`

### 進度條
- **背景**: `rgba(255, 255, 255, 0.1)`
- **填充**: 黃色 `#F5C451`
- **高度**: 8px
- **圓角**: 4px

## 🎯 通用設計規範

### 字體系統
- **主字體**: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
- **Dashboard 字體**: 'Noto Sans', 'Helvetica Neue', Arial, sans-serif
- **行高**: 1.6
- **字重**: 
  - 正常: 400
  - 中等: 500  
  - 粗體: 600
  - 超粗: 700

### 圓角系統
- **標準圓角**: 8px
- **小圓角**: 4px, 6px
- **大圓角**: 20px (特殊用途)

### 陰影系統
- **淺色主題**: `0 4px 20px rgba(0, 0, 0, 0.1)`
- **深色主題**: `0 4px 20px rgba(0, 0, 0, 0.3)`

### 動畫效果
- **標準過渡**: `all 0.3s ease`
- **按鈕 hover**: `translateY(-1px)` 或 `translateY(-2px)`
- **卡片 hover**: `translateY(-2px)` 或 `translateY(-5px)`
- **載入動畫**: 2s 線性無限旋轉

### 間距系統
- **頁面內邊距**: 20px, 30px
- **卡片內邊距**: 25px, 40px
- **按鈮內邊距**: 12px 20px (標準), 15px 30px (大型)
- **元素間距**: 15px, 20px, 30px, 40px, 60px

## 📱 響應式設計

### 斷點
- **桌面**: > 768px
- **平板**: ≤ 768px  
- **手機**: ≤ 480px

### 行動裝置適配
- 側邊欄變為滑動式選單
- 卡片網格改為單欄
- 字體大小縮減
- 間距調整

## 🎨 圖標系統
- **主要使用**: Font Awesome 圖標
- **顏色**: 
  - Landing: `#71c9f1`
  - Dashboard: `#F5C451`
- **大小**: 16px (選單), 40px-50px (卡片), 48px (功能區)

## 🔧 技術實作注意事項

### CSS 變數命名
- 使用語義化命名
- 區分淺色/深色主題
- 保持一致性

### 狀態管理
- hover 狀態必須有視覺回饋
- focus 狀態需要明確指示
- disabled 狀態要明顯區分

### 可訪問性
- 確保對比度符合 WCAG 標準
- 提供鍵盤導航支援
- 適當的 aria 標籤

---

**文件版本**: 1.1  
**最後更新**: 2025/01/31  
**更新內容**: 
- 修復首頁 Footer 配色統一問題 (深藍色背景 + 淺藍色強調色)
- Dashboard Header 和 Sidebar 統一使用淺藍色背景 (#71c9f1)
- 統計數字改為淺藍色，保持與原始設計一致
- 完善響應式設計和可訪問性  
**基於**: 原始 app/static 和 app/templates 檔案分析 + Next.js 重構實作
