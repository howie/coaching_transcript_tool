#!/bin/bash

# Configuration Environment Checker - Shell Wrapper
# 配置環境檢查工具的 Shell 包裝腳本
#
# 使用方式:
#   ./check-config.sh comprehensive
#   ./check-config.sh security-audit
#   ./check-config.sh compare development production
#   ./check-config.sh terraform-check production

set -euo pipefail

# 腳本常數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_CHECKER="$SCRIPT_DIR/config-checker.py"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輔助函數
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

show_header() {
    echo -e "${BLUE}"
    echo "╭─────────────────────────────────────────────────────────────╮"
    echo "│                Configuration Environment Checker             │"
    echo "│                    配置環境檢查工具                         │"
    echo "╰─────────────────────────────────────────────────────────────╯"
    echo -e "${NC}"
}

show_usage() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
  comprehensive                     執行全面配置檢查 (推薦)
  security-audit                   專注安全性審核
  compare <env1> <env2>            比較兩個環境配置
  terraform-check <environment>    驗證 Terraform 一致性
  validate <environment>           驗證單一環境配置
  discover                         發現並列出所有配置檔案
  report [output-file]             生成詳細報告

Examples:
  $0 comprehensive                 # 檢查所有環境
  $0 comprehensive -e dev,prod     # 只檢查開發和生產環境
  $0 security-audit               # 安全性審核
  $0 compare development production # 比較開發與生產環境
  $0 terraform-check production    # 檢查生產環境 Terraform 一致性
  $0 validate development          # 驗證開發環境配置
  $0 report config-audit.md        # 生成報告到指定檔案

Options:
  -h, --help                      顯示此幫助訊息
  -e, --environments <envs>       指定環境 (逗號分隔)
  -o, --output <file>             報告輸出檔案
  --project-root <path>           專案根目錄
  --no-color                      停用顏色輸出

EOF
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # 檢查 Python
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # 檢查配置檢查器腳本
    if [[ ! -f "$CONFIG_CHECKER" ]]; then
        log_error "Configuration checker script not found: $CONFIG_CHECKER"
        exit 1
    fi
    
    # 檢查專案根目錄
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        log_error "Project root directory not found: $PROJECT_ROOT"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

run_comprehensive_check() {
    local environments=""
    local output_file=""
    
    # 解析選項
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environments)
                environments="$2"
                shift 2
                ;;
            -o|--output)
                output_file="$2"
                shift 2
                ;;
            *)
                log_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    log_info "Starting comprehensive configuration check..."
    
    local cmd="python3 '$CONFIG_CHECKER' --comprehensive --project-root '$PROJECT_ROOT'"
    
    if [[ -n "$environments" ]]; then
        cmd="$cmd --environments '$environments'"
        log_info "Checking environments: $environments"
    fi
    
    if [[ -n "$output_file" ]]; then
        cmd="$cmd --output '$output_file'"
        log_info "Report will be saved to: $output_file"
    fi
    
    # 執行檢查
    if eval "$cmd"; then
        log_success "Configuration check completed successfully"
        return 0
    else
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            log_error "Critical configuration issues found!"
        elif [[ $exit_code -eq 1 ]]; then
            log_warning "High priority configuration issues found"
        fi
        return $exit_code
    fi
}

run_security_audit() {
    log_info "Starting security audit..."
    
    # 簡化版安全檢查實作
    log_info "Checking for common security issues..."
    
    # 檢查是否存在 .env 檔案在版本控制中
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        log_warning "Found .env file in project root - ensure it's in .gitignore"
    fi
    
    # 檢查是否有明顯的密鑰暴露
    local sensitive_patterns=(
        "password\s*=\s*['\"]?123456"
        "secret.*['\"]?(test|demo|example)"
        "key.*['\"]?(changeme|default)"
    )
    
    log_info "Scanning for exposed secrets in configuration files..."
    
    for pattern in "${sensitive_patterns[@]}"; do
        if grep -r -i -E "$pattern" "$PROJECT_ROOT" --include="*.env*" --include="*.tfvars" 2>/dev/null; then
            log_warning "Potential security issue found: $pattern"
        fi
    done
    
    log_success "Security audit completed"
}

compare_environments() {
    if [[ $# -lt 2 ]]; then
        log_error "Usage: $0 compare <env1> <env2>"
        exit 1
    fi
    
    local env1="$1"
    local env2="$2"
    
    log_info "Comparing $env1 vs $env2 environments..."
    
    python3 "$CONFIG_CHECKER" \
        --comprehensive \
        --environments "$env1,$env2" \
        --project-root "$PROJECT_ROOT"
}

validate_terraform() {
    if [[ $# -lt 1 ]]; then
        log_error "Usage: $0 terraform-check <environment>"
        exit 1
    fi
    
    local environment="$1"
    
    log_info "Validating Terraform consistency for $environment environment..."
    
    python3 "$CONFIG_CHECKER" \
        --validate-terraform \
        --environment "$environment" \
        --project-root "$PROJECT_ROOT"
}

discover_configs() {
    log_info "Discovering configuration files..."
    
    echo -e "\n${BLUE}📁 Configuration Files Found:${NC}"
    
    # .env 檔案
    while IFS= read -r -d '' file; do
        echo "  📄 $(basename "$file") -> $(realpath --relative-to="$PROJECT_ROOT" "$file")"
    done < <(find "$PROJECT_ROOT" -name ".env*" -type f -print0 2>/dev/null)
    
    # terraform.tfvars 檔案
    while IFS= read -r -d '' file; do
        echo "  ⚙️  $(basename "$file") -> $(realpath --relative-to="$PROJECT_ROOT" "$file")"
    done < <(find "$PROJECT_ROOT" -name "terraform.tfvars*" -type f -print0 2>/dev/null)
    
    echo ""
}

generate_report() {
    local output_file="${1:-config-report-$(date +%Y%m%d_%H%M%S).md}"
    
    log_info "Generating configuration report..."
    
    python3 "$CONFIG_CHECKER" \
        --comprehensive \
        --generate-report \
        --output "$output_file" \
        --project-root "$PROJECT_ROOT"
    
    if [[ -f "$output_file" ]]; then
        log_success "Report generated: $output_file"
        
        # 如果有 markdown 預覽器可用，詢問是否要開啟
        if command -v mdcat >/dev/null 2>&1; then
            echo -e "\n${BLUE}📖 Preview report? (y/n):${NC} \c"
            read -r answer
            if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
                mdcat "$output_file"
            fi
        fi
    else
        log_error "Failed to generate report"
        exit 1
    fi
}

validate_single_environment() {
    if [[ $# -lt 1 ]]; then
        log_error "Usage: $0 validate <environment>"
        exit 1
    fi
    
    local environment="$1"
    
    log_info "Validating $environment environment configuration..."
    
    python3 "$CONFIG_CHECKER" \
        --comprehensive \
        --environments "$environment" \
        --project-root "$PROJECT_ROOT"
}

# 主函數
main() {
    # 處理全域選項
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-color)
                RED=""
                GREEN=""
                YELLOW=""
                BLUE=""
                NC=""
                shift
                ;;
            -h|--help)
                show_header
                show_usage
                exit 0
                ;;
            --project-root)
                PROJECT_ROOT="$2"
                shift 2
                ;;
            -*)
                # 其他選項將傳遞給子命令
                break
                ;;
            *)
                # 第一個非選項參數是命令
                break
                ;;
        esac
    done
    
    if [[ $# -eq 0 ]]; then
        show_header
        show_usage
        exit 0
    fi
    
    # 顯示標題
    show_header
    
    # 檢查前置條件
    check_prerequisites
    
    # 解析命令
    local command="$1"
    shift
    
    case "$command" in
        comprehensive)
            run_comprehensive_check "$@"
            ;;
        security-audit)
            run_security_audit "$@"
            ;;
        compare)
            compare_environments "$@"
            ;;
        terraform-check)
            validate_terraform "$@"
            ;;
        validate)
            validate_single_environment "$@"
            ;;
        discover)
            discover_configs "$@"
            ;;
        report)
            generate_report "$@"
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"