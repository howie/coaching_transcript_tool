#!/bin/bash

# 環境變數轉換工具 - Shell 包裝器
# 使用方式: ./convert-env.sh [env-file] [environment]

set -e

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

# 預設值
ENV_FILE=${1:-".env.prod"}
ENVIRONMENT=${2:-"production"}

# 腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "🔄 環境變數轉換工具"
echo "=================="

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    log_error "需要 Python 3"
    exit 1
fi

# 檢查環境檔案
if [ ! -f "$ENV_FILE" ]; then
    log_error "環境檔案不存在: $ENV_FILE"
    echo ""
    echo "請提供 .env.prod 檔案路徑，或創建包含以下變數的檔案:"
    echo ""
    echo "# Cloudflare"
    echo "CLOUDFLARE_API_TOKEN=your-token"
    echo "CLOUDFLARE_ZONE_ID=your-zone-id"
    echo "CLOUDFLARE_ACCOUNT_ID=your-account-id"
    echo ""
    echo "# Render"
    echo "RENDER_API_KEY=your-api-key"
    echo ""
    echo "# ECPay"
    echo "ECPAY_MERCHANT_ID=your-merchant-id"
    echo "ECPAY_HASH_KEY=your-hash-key"
    echo "ECPAY_HASH_IV=your-hash-iv"
    echo ""
    exit 1
fi

log_info "環境檔案: $ENV_FILE"
log_info "目標環境: $ENVIRONMENT"

# 切換到 terraform 目錄
cd "$SCRIPT_DIR/.."

# 執行轉換
log_info "開始轉換..."

python3 "$SCRIPT_DIR/env-to-tfvars.py" \
    --env-file "$ENV_FILE" \
    --environment "$ENVIRONMENT" \
    --template "environments/$ENVIRONMENT/terraform.tfvars.example"

if [ $? -eq 0 ]; then
    log_success "轉換完成!"
    echo ""
    echo "📁 輸出檔案: environments/$ENVIRONMENT/terraform.tfvars"
    echo ""
    echo "🔍 請檢查生成的檔案並確認所有值都正確"
    echo ""
    echo "🚀 下一步驟:"
    echo "   cd environments/$ENVIRONMENT"
    echo "   terraform init"
    echo "   terraform plan"
    echo ""
else
    log_error "轉換失敗"
    exit 1
fi