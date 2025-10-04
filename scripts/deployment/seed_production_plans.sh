#!/bin/bash
# Production Plan Seeding Script
#
# This script safely seeds plan configurations to production database.
# It includes safety checks, backups, and verification steps.
#
# Usage:
#   ./scripts/deployment/seed_production_plans.sh
#
# Prerequisites:
#   - DATABASE_URL environment variable set to production database
#   - Python environment with required packages
#   - Backup permissions on database

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/tmp/db_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/plan_configurations_backup_$TIMESTAMP.sql"

# Functions
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

print_header() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}$1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

check_prerequisites() {
    print_header "1. Checking Prerequisites"

    # Check DATABASE_URL
    if [ -z "$DATABASE_URL" ]; then
        log_error "DATABASE_URL environment variable is not set"
        echo ""
        echo "Please set it using one of these methods:"
        echo ""
        echo "Option 1 - From Render Dashboard:"
        echo "  1. Go to https://dashboard.render.com/d/dpg-d27igr7diees73cla8og-a"
        echo "  2. Copy the 'External Database URL'"
        echo "  3. Run: export DATABASE_URL='<copied-url>'"
        echo ""
        echo "Option 2 - From Render API Service:"
        echo "  1. Go to https://dashboard.render.com/web/srv-d2sndkh5pdvs739lqq0g"
        echo "  2. Click 'Environment' tab"
        echo "  3. Find DATABASE_URL value"
        echo "  4. Run: export DATABASE_URL='<value>'"
        echo ""
        exit 1
    fi

    log_success "DATABASE_URL is set"

    # Verify it's a PostgreSQL URL
    if [[ ! "$DATABASE_URL" =~ ^postgres(ql)?:// ]]; then
        log_error "DATABASE_URL doesn't appear to be a PostgreSQL connection string"
        exit 1
    fi

    log_success "DATABASE_URL format is valid"

    # Check Python
    if ! command -v python &> /dev/null; then
        log_error "Python is not installed"
        exit 1
    fi

    log_success "Python is available: $(python --version)"

    # Check psql (optional but recommended for backup)
    if command -v psql &> /dev/null; then
        log_success "psql is available: $(psql --version | head -1)"
    else
        log_warning "psql not found - backup will be skipped"
    fi

    # Check seed script exists
    if [ ! -f "$PROJECT_ROOT/scripts/database/seed_plan_configurations_v2.py" ]; then
        log_error "Seed script not found at scripts/database/seed_plan_configurations_v2.py"
        exit 1
    fi

    log_success "Seed script found"
}

verify_database_connection() {
    print_header "2. Verifying Database Connection"

    log_info "Testing connection to database..."

    # Try to connect and get database name
    DB_NAME=$(psql "$DATABASE_URL" -t -c "SELECT current_database();" 2>&1 | xargs || echo "")

    if [ -z "$DB_NAME" ]; then
        log_error "Could not connect to database"
        log_error "Please verify DATABASE_URL is correct and accessible"
        exit 1
    fi

    log_success "Connected to database: $DB_NAME"

    # Get current plan count
    CURRENT_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM plan_configurations;" 2>/dev/null | xargs || echo "0")

    log_info "Current plan_configurations count: $CURRENT_COUNT"

    if [ "$CURRENT_COUNT" -gt 0 ]; then
        log_warning "Database already has $CURRENT_COUNT plan configurations"
        log_warning "Running seed script will DELETE and REPLACE them"
        echo ""
        read -p "Do you want to continue? (yes/no): " -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
            log_info "Aborted by user"
            exit 0
        fi
    else
        log_info "Database is empty - safe to seed"
    fi
}

backup_existing_plans() {
    print_header "3. Backing Up Existing Plans"

    if ! command -v psql &> /dev/null; then
        log_warning "Skipping backup - psql not available"
        return 0
    fi

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    log_info "Creating backup at: $BACKUP_FILE"

    # Backup plan_configurations table
    psql "$DATABASE_URL" -c "\COPY (SELECT * FROM plan_configurations) TO '$BACKUP_FILE' WITH CSV HEADER;" 2>&1

    if [ -f "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(wc -l < "$BACKUP_FILE" | xargs)
        log_success "Backup created: $((BACKUP_SIZE - 1)) rows saved"
    else
        log_warning "Backup file not created (table might be empty)"
    fi
}

run_seed_script() {
    print_header "4. Running Seed Script"

    log_info "Executing: python scripts/database/seed_plan_configurations_v2.py"
    echo ""

    cd "$PROJECT_ROOT"

    # Run the seed script
    if python scripts/database/seed_plan_configurations_v2.py; then
        log_success "Seed script completed successfully"
    else
        log_error "Seed script failed"

        if [ -f "$BACKUP_FILE" ]; then
            echo ""
            log_info "To restore from backup, run:"
            echo "  psql \$DATABASE_URL -c \"\\COPY plan_configurations FROM '$BACKUP_FILE' WITH CSV HEADER;\""
        fi

        exit 1
    fi
}

verify_seeding() {
    print_header "5. Verifying Seed Results"

    # Count plans
    FINAL_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM plan_configurations;" 2>/dev/null | xargs || echo "0")

    log_info "Final plan count: $FINAL_COUNT"

    if [ "$FINAL_COUNT" -eq 4 ]; then
        log_success "Expected number of plans (4) found"
    else
        log_error "Unexpected plan count: $FINAL_COUNT (expected 4)"
        exit 1
    fi

    # Verify all are active and visible
    ACTIVE_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM plan_configurations WHERE is_active = true AND is_visible = true;" 2>/dev/null | xargs || echo "0")

    if [ "$ACTIVE_COUNT" -eq 4 ]; then
        log_success "All plans are active and visible"
    else
        log_warning "Only $ACTIVE_COUNT plans are active and visible"
    fi

    # Show plan summary
    echo ""
    log_info "Plan Summary:"
    psql "$DATABASE_URL" -c "SELECT plan_type, plan_name, display_name, is_active, is_visible, sort_order FROM plan_configurations ORDER BY sort_order;" 2>/dev/null || true
}

test_api_endpoint() {
    print_header "6. Testing API Endpoint (Optional)"

    log_info "To test the API endpoint, run:"
    echo ""
    echo "  curl -s 'https://coachly.doxa.com.tw/api/proxy/v1/plans' \\"
    echo "    -H 'Authorization: Bearer <YOUR_TOKEN>' | jq '.total'"
    echo ""
    log_info "Expected result: 4"
    echo ""

    log_info "To get your token:"
    echo "  1. Open https://coachly.doxa.com.tw in browser"
    echo "  2. Open DevTools (F12) → Console"
    echo "  3. Run: localStorage.getItem('auth_token')"
}

print_completion_summary() {
    print_header "✅ Deployment Complete"

    echo "Summary:"
    echo "  • Plans seeded: 4"
    echo "  • Backup location: $BACKUP_FILE"
    echo "  • Database: $(psql "$DATABASE_URL" -t -c "SELECT current_database();" 2>/dev/null | xargs)"
    echo ""

    log_success "Production plans have been seeded successfully!"
    echo ""

    echo "Next Steps:"
    echo "  1. Verify frontend: https://coachly.doxa.com.tw/dashboard/billing"
    echo "  2. Check logs: render logs srv-d2sndkh5pdvs739lqq0g --limit 50 --text 'plans'"
    echo "  3. Test subscription flow with a user account"
    echo ""
}

# Main execution
main() {
    clear
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║        🌱 Production Plan Seeding Script                  ║"
    echo "║                                                            ║"
    echo "║        Database: Coachly-db-production                     ║"
    echo "║        Plans: FREE, STUDENT, PRO, COACHING_SCHOOL          ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    check_prerequisites
    verify_database_connection
    backup_existing_plans
    run_seed_script
    verify_seeding
    test_api_endpoint
    print_completion_summary
}

# Run main function
main "$@"
