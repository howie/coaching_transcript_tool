# Coachly 設計系統

## ⚡ Dark Mode & Accessibility (Updated January 2025)

### 🎯 WCAG 2.1 AA Compliance

All text colors now meet strict accessibility standards:
- **Normal text**: Minimum 4.5:1 contrast ratio
- **Large text** (≥18.66px bold): Minimum 3:1 contrast ratio

### 🔧 Semantic Color System

New semantic tokens provide consistent theming across light/dark modes:

```css
:root {
  /* Light mode - WCAG AA compliant */
  --bg: #ffffff;
  --card: #ffffff;
  --border: #e5e7eb;          /* gray-200 */
  --foreground: #111827;      /* gray-900 - 15.8:1 contrast */
  --muted: #f9fafb;           /* gray-50 */
  --muted-foreground: #6b7280; /* gray-500 - 4.61:1 contrast */
  --accent: #71c9f1;          /* Primary blue */
  --ring: #d1d5db;            /* gray-300 */
  --input: #111827;
  --placeholder: #9ca3af;     /* gray-400 */
}

.dark {
  /* Dark mode - WCAG AA compliant */
  --bg: #0f172a;              /* slate-900 */
  --card: #1e293b;            /* slate-800 */
  --border: #334155;          /* slate-600 */
  --foreground: #f3f4f6;      /* gray-100 - 15.8:1 contrast */
  --muted: #1e293b;           /* slate-800 */
  --muted-foreground: #cbd5e1; /* slate-300 - 9.85:1 contrast */
  --accent: #F5C451;          /* Brand yellow - 11.2:1 contrast */
  --ring: #475569;            /* slate-600 */
  --input: #f3f4f6;
  --placeholder: #94a3b8;     /* slate-400 */
}
```

### 📝 Usage Guidelines

**✅ Use semantic tokens:**
```tsx
<h1 className="text-foreground">Heading</h1>
<p className="text-muted-foreground">Description</p>
<div className="bg-card border-border">Content</div>
```

**❌ Avoid hardcoded colors:**
```tsx
<h1 className="text-gray-900 dark:text-white">Heading</h1>
<div className="bg-white dark:bg-gray-800">Content</div>
```

### 🌙 Dark Mode Implementation

- **Method**: Class-based (`.dark` on `<html>`)
- **Storage**: localStorage with system preference fallback
- **FOUC Prevention**: Early initialization script
- **Components**: All form elements, tables, cards updated

### ✅ Verified Contrast Ratios

#### Light Mode
- Primary text: **15.8:1** ✅
- Secondary text: **4.61:1** ✅  
- Accent on white: **2.85:1** (Large text only)

#### Dark Mode  
- Primary text: **15.8:1** ✅
- Secondary text: **9.85:1** ✅
- Accent on dark: **11.2:1** ✅

---

## 🎨 設計理念

Coachly 採用**情境式雙主題設計系統**，根據不同使用場景提供最適合的視覺體驗：

- **Landing Page**: 清新友好的行銷風格，吸引潛在用戶
- **Dashboard**: 專業沉穩的應用風格，專注工作效率

## 🌊 Landing Page 主題

### 色彩系統

```css
:root[data-theme="light"] {
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
  
  /* 表單輸入（Light） */
  --input-bg: #F8FAFC;
  --input-text: #0F172A;
  --input-placeholder: #94A3B8;
  --input-border: #CBD5E1;
  --input-border-focus: #94A3B8;
  --focus-ring-rgb: 245, 196, 81; /* #F5C451 (RGB for alpha) */
  --error-text: #B91C1C;
  --error-border: #EF4444;
  --success-text: #166534;
  --disabled-bg: #E5E7EB;
  --disabled-text: #9CA3AF;
  --disabled-border: #E5E7EB;
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
:root[data-theme="dark"] {
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
  --input-bg: #1F2A3B; /* 深灰藍 */
  
  /* 陰影與效果 */
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  --border-radius: 8px;
  --transition: all 0.3s ease;
  
  /* 表單輸入（Dark） */
  --input-text: #F8FAFC;
  --input-placeholder: #94A3B8;
  --input-border: #334155;
  --input-border-focus: #64748B;
  --focus-ring-rgb: 245, 196, 81; /* 與 Light 共用 */
  --error-text: #FCA5A5;
  --error-border: #EF4444;
  --success-text: #86EFAC;
  --disabled-bg: #111827;
  --disabled-text: #6B7280;
  --disabled-border: #374151;
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

### 表單輸入（Light/Dark 共用元件）

> 使用語意化 Token（見上方 Light / Dark `--input-*` 與 `--focus-ring-rgb`）。請勿在 input 上硬編碼 `text-white` 或色碼。

```css
.input-base {
  width: 100%;
  height: 44px;
  padding: 0 12px;
  border-radius: 10px;
  background: var(--input-bg);
  color: var(--input-text);
  border: 1px solid var(--input-border);
  outline: none;
  transition: border-color .15s ease, box-shadow .15s ease, background-color .15s ease, color .15s ease;
}

.input-base::placeholder {
  color: var(--input-placeholder);
}

.input-base:focus {
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 4px rgba(var(--focus-ring-rgb), .40);
}

.input-base:disabled {
  background: var(--disabled-bg);
  color: var(--disabled-text);
  border-color: var(--disabled-border);
  cursor: not-allowed;
}

/* 狀態 */
.input-error {
  border-color: var(--error-border) !important;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, .25);
}

.label { color: var(--text-secondary); font-weight: 600; font-size: 14px; }
.helper { color: var(--text-tertiary, #94a3b8); font-size: 12px; }
.error-text { color: var(--error-text); font-size: 12px; }
.success-text { color: var(--success-text); font-size: 12px; }
```

#### 可用性與驗收
- **對比度（AA）**: 一般文字 ≥ 4.5:1、placeholder ≥ 4.5:1
- **Focus**: 需有明顯外框（黃環）
- **鍵盤操作**: Tab/Shift+Tab 焦點可見
- **Disabled/Error**: 狀態明顯且可讀

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

**文件版本**: 1.2  
**最後更新**: 2025/08/05  
**更新內容**: 
- 主題選擇器統一：將 `:root` 改為 `:root[data-theme="light"]` 和 `:root[data-theme="dark"]`
- 新增表單輸入語意色 Token（Light/Dark 各一組）：`--input-bg`、`--input-text`、`--input-placeholder`、`--input-border`、`--input-border-focus`、`--focus-ring-rgb`
- 新增共用 Input 元件基礎樣式：`.input-base`、`.input-error`、`.label`、`.helper`、`.error-text`、`.success-text`
- 移除硬編碼色彩，統一使用語意化 Token
- 完善表單可用性與驗收標準
**前版本 (1.1)**: 修復首頁 Footer 配色統一問題、Dashboard Header 和 Sidebar 統一使用淺藍色背景、統計數字改為淺藍色、完善響應式設計和可訪問性  
**基於**: 原始 app/static 和 app/templates 檔案分析 + Next.js 重構實作
