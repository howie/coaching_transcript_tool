#!/usr/bin/env python3
"""
Progress to Changelog Synchronization Script

根據 .clinerules/progress-changelog-rules.md 規則，
將 memory-bank/progress.md 中的已完成項目移至 docs/changelog.md

功能：
1. 解析 progress.md 的 Markdown 結構
2. 識別已完成項目（✅ 標記）
3. 生成 changelog 格式的快照記錄
4. 更新兩個文件並保持格式完整性
5. 支援 dry-run 預覽模式

使用方式：
    python scripts/sync_progress_to_changelog.py [--dry-run] [--verbose]
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# 文件路徑配置
PROGRESS_FILE = Path("memory-bank/progress.md")
CHANGELOG_FILE = Path("docs/changelog.md")

class ProgressItem:
    """表示一個進度項目"""
    def __init__(self, content: str, section: str, date: str):
        self.content = content.strip()
        self.section = section
        self.date = date
        self.is_completed = self._check_completed()
    
    def _check_completed(self) -> bool:
        """檢查是否為已完成項目"""
        # 檢查是否包含 ✅ 標記
        return "✅" in self.content
    
    def to_changelog_format(self) -> str:
        """轉換為 changelog 格式"""
        # 移除多餘前綴和格式化
        cleaned = re.sub(r'^[\s\-\*]*', '', self.content)
        cleaned = re.sub(r'^\*\*([^*]+)\*\*', r'- ✅ \1', cleaned)
        if not cleaned.startswith('- ✅'):
            cleaned = f"- ✅ {cleaned}"
        return cleaned

class ProgressParser:
    """解析 progress.md 文件"""
    
    def __init__(self, content: str):
        self.content = content
        self.items: List[ProgressItem] = []
        self.sections: Dict[str, List[str]] = {}
        
    def parse(self) -> None:
        """解析進度文件"""
        lines = self.content.split('\n')
        current_section = ""
        current_date = ""
        current_item_lines = []
        
        for line in lines:
            # 檢測日期標題 (## 2025-08-03)
            date_match = re.match(r'^## (\d{4}-\d{2}-\d{2})', line)
            if date_match:
                current_date = date_match.group(1)
                current_section = f"## {current_date}"
                continue
            
            # 檢測子標題 (### 已完成, ### 待辦等)
            section_match = re.match(r'^### (.+)', line)
            if section_match:
                current_section = section_match.group(1)
                continue
            
            # 收集項目內容
            if line.strip() and not line.startswith('#'):
                # 如果是新的項目（以 - 或 * 開始），保存之前的項目
                if re.match(r'^[\s]*[\-\*]', line) and current_item_lines:
                    item_content = '\n'.join(current_item_lines)
                    if item_content.strip():
                        item = ProgressItem(item_content, current_section, current_date)
                        self.items.append(item)
                    current_item_lines = [line]
                else:
                    current_item_lines.append(line)
        
        # 處理最後一個項目
        if current_item_lines:
            item_content = '\n'.join(current_item_lines)
            if item_content.strip():
                item = ProgressItem(item_content, current_section, current_date)
                self.items.append(item)
    
    def get_completed_items(self) -> List[ProgressItem]:
        """獲取已完成項目"""
        return [item for item in self.items if item.is_completed]
    
    def get_active_items(self) -> List[ProgressItem]:
        """獲取活躍項目（未完成）"""
        return [item for item in self.items if not item.is_completed]

class ChangelogGenerator:
    """生成 changelog 內容"""
    
    def __init__(self, completed_items: List[ProgressItem]):
        self.completed_items = completed_items
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def generate_snapshot(self) -> str:
        """生成進度快照"""
        if not self.completed_items:
            return ""
        
        snapshot_lines = [f"## {self.today} Progress Snapshot"]
        
        # 按日期分組
        date_groups = {}
        for item in self.completed_items:
            date = item.date or "未分類"
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(item)
        
        # 生成分組內容
        for date, items in sorted(date_groups.items(), reverse=True):
            if date != "未分類":
                snapshot_lines.append(f"### {date} 完成項目")
            else:
                snapshot_lines.append("### 其他完成項目")
            
            for item in items:
                changelog_line = item.to_changelog_format()
                snapshot_lines.append(changelog_line)
                
                # 添加詳細內容（如果有多行）
                if '\n' in item.content:
                    detail_lines = item.content.split('\n')[1:]
                    for detail in detail_lines:
                        if detail.strip() and not detail.strip().startswith('-'):
                            snapshot_lines.append(f"  - {detail.strip()}")
            
            snapshot_lines.append("")  # 空行分隔
        
        return '\n'.join(snapshot_lines)

class ProgressCleaner:
    """清理 progress.md 文件"""
    
    def __init__(self, content: str, completed_items: List[ProgressItem]):
        self.content = content
        self.completed_items = completed_items
    
    def clean_progress(self) -> str:
        """移除已完成項目，保留活躍內容"""
        lines = self.content.split('\n')
        cleaned_lines = []
        skip_lines = False
        current_section_empty = True
        section_header = None
        
        for line in lines:
            # 檢測章節標題
            if re.match(r'^##+ ', line):
                # 添加之前的章節（如果不為空）
                if section_header and not current_section_empty:
                    cleaned_lines.extend(section_header)
                
                section_header = [line]
                current_section_empty = True
                skip_lines = False
                continue
            
            # 檢查是否為已完成項目
            is_completed_item = any(
                item.content.strip() in line or line.strip() in item.content
                for item in self.completed_items
            )
            
            if is_completed_item:
                skip_lines = True
                continue
            
            # 如果不是已完成項目，且不是空行，標記章節為非空
            if line.strip():
                current_section_empty = False
                skip_lines = False
            
            if not skip_lines:
                if section_header:
                    cleaned_lines.extend(section_header)
                    section_header = None
                cleaned_lines.append(line)
        
        # 添加最後的章節
        if section_header and not current_section_empty:
            cleaned_lines.extend(section_header)
        
        # 清理多餘的空行
        result = []
        prev_empty = False
        for line in cleaned_lines:
            if line.strip():
                result.append(line)
                prev_empty = False
            elif not prev_empty:
                result.append(line)
                prev_empty = True
        
        return '\n'.join(result)

def read_file_safe(filepath: Path) -> str:
    """安全讀取文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
        return ""
    except Exception as e:
        print(f"❌ 讀取文件失敗 {filepath}: {e}")
        return ""

def write_file_safe(filepath: Path, content: str, dry_run: bool = False) -> bool:
    """安全寫入文件"""
    if dry_run:
        print(f"🔍 [DRY-RUN] 將寫入 {filepath}")
        return True
    
    try:
        # 確保目錄存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 成功寫入: {filepath}")
        return True
    except Exception as e:
        print(f"❌ 寫入文件失敗 {filepath}: {e}")
        return False

def update_changelog(existing_content: str, new_snapshot: str) -> str:
    """更新 changelog 內容"""
    if not new_snapshot.strip():
        return existing_content
    
    # 在第一個 ## 標題前插入新快照
    lines = existing_content.split('\n')
    
    # 找到第一個 ## 標題位置
    insert_pos = 0
    for i, line in enumerate(lines):
        if re.match(r'^## ', line):
            insert_pos = i
            break
    
    # 插入新內容
    new_lines = lines[:insert_pos] + [new_snapshot, ""] + lines[insert_pos:]
    return '\n'.join(new_lines)

def main():
    parser = argparse.ArgumentParser(description="同步 progress.md 已完成項目到 changelog.md")
    parser.add_argument('--dry-run', action='store_true', help='預覽模式，不實際修改文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    print("🚀 Progress to Changelog 同步工具")
    print("=" * 50)
    
    # 檢查文件存在性
    if not PROGRESS_FILE.exists():
        print(f"❌ Progress 文件不存在: {PROGRESS_FILE}")
        sys.exit(1)
    
    # 讀取 progress.md
    print(f"📖 讀取 {PROGRESS_FILE}")
    progress_content = read_file_safe(PROGRESS_FILE)
    if not progress_content:
        print("❌ Progress 文件為空或讀取失敗")
        sys.exit(1)
    
    # 解析進度項目
    print("🔍 解析進度項目...")
    parser = ProgressParser(progress_content)
    parser.parse()
    
    completed_items = parser.get_completed_items()
    active_items = parser.get_active_items()
    
    print(f"📊 統計結果:")
    print(f"   - 已完成項目: {len(completed_items)}")
    print(f"   - 活躍項目: {len(active_items)}")
    
    if args.verbose:
        print("\n📋 已完成項目列表:")
        for i, item in enumerate(completed_items, 1):
            print(f"   {i}. {item.content[:50]}..." if len(item.content) > 50 else f"   {i}. {item.content}")
    
    if not completed_items:
        print("ℹ️ 沒有找到已完成項目，無需同步")
        return
    
    # 生成 changelog 快照
    print("📝 生成 changelog 快照...")
    changelog_gen = ChangelogGenerator(completed_items)
    new_snapshot = changelog_gen.generate_snapshot()
    
    if args.verbose:
        print("\n📋 生成的快照預覽:")
        print("-" * 30)
        print(new_snapshot[:500] + "..." if len(new_snapshot) > 500 else new_snapshot)
        print("-" * 30)
    
    # 讀取並更新 changelog
    print(f"📖 讀取 {CHANGELOG_FILE}")
    existing_changelog = read_file_safe(CHANGELOG_FILE)
    updated_changelog = update_changelog(existing_changelog, new_snapshot)
    
    # 清理 progress.md
    print("🧹 清理 progress.md...")
    cleaner = ProgressCleaner(progress_content, completed_items)
    cleaned_progress = cleaner.clean_progress()
    
    # 寫入文件
    print(f"\n{'🔍 [DRY-RUN] ' if args.dry_run else '💾 '}寫入更新...")
    
    success = True
    success &= write_file_safe(CHANGELOG_FILE, updated_changelog, args.dry_run)
    success &= write_file_safe(PROGRESS_FILE, cleaned_progress, args.dry_run)
    
    if success:
        print("🎉 同步完成！")
        if args.dry_run:
            print("💡 使用 --dry-run 預覽模式，實際文件未修改")
            print("💡 移除 --dry-run 參數以執行實際同步")
    else:
        print("❌ 同步過程中出現錯誤")
        sys.exit(1)

if __name__ == "__main__":
    main()
