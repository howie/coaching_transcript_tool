#!/bin/bash

# List and manage Terraform state backups
# Usage: ./list-backups.sh [environment] [action]

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
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

log_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Arguments
ENVIRONMENT=${1:-"all"}
ACTION=${2:-"list"}

echo "📋 Terraform State Backup Management"
echo "====================================="

# Validate action
case $ACTION in
    list|clean|verify|stats)
        log_info "Action: $ACTION"
        ;;
    *)
        log_error "Invalid action: $ACTION"
        echo "Valid actions: list, clean, verify, stats"
        exit 1
        ;;
esac

BACKUP_DIR="backups/state"

if [ ! -d "$BACKUP_DIR" ]; then
    log_warning "No backup directory found: $BACKUP_DIR"
    echo "Run ./scripts/backup-state.sh to create your first backup"
    exit 0
fi

# Function to format file size
format_size() {
    local size=$1
    if [ "$size" -ge 1048576 ]; then
        echo "$((size / 1048576))MB"
    elif [ "$size" -ge 1024 ]; then
        echo "$((size / 1024))KB"
    else
        echo "${size}B"
    fi
}

# Function to get file age
get_file_age() {
    local file=$1
    local file_time=$(stat -f %m "$file" 2>/dev/null || stat -c %Y "$file" 2>/dev/null)
    local current_time=$(date +%s)
    local age=$((current_time - file_time))
    
    if [ $age -lt 3600 ]; then
        echo "$((age / 60))m ago"
    elif [ $age -lt 86400 ]; then
        echo "$((age / 3600))h ago"
    else
        echo "$((age / 86400))d ago"
    fi
}

# Function to validate backup file
validate_backup() {
    local file=$1
    if [ ! -f "$file" ]; then
        echo "MISSING"
        return 1
    fi
    
    if ! jq empty "$file" 2>/dev/null; then
        echo "INVALID"
        return 1
    fi
    
    local resources=$(jq '.resources | length' "$file" 2>/dev/null || echo "0")
    echo "OK ($resources resources)"
    return 0
}

# Function to list backups for specific environment
list_environment_backups() {
    local env=$1
    local files=$(ls -t "$BACKUP_DIR"/terraform-$env-*.tfstate 2>/dev/null || echo "")
    
    if [ -z "$files" ]; then
        log_warning "No backups found for environment: $env"
        return
    fi
    
    log_header "🏷️  $env Environment Backups"
    echo "----------------------------------------"
    
    local count=0
    echo "$files" | while read -r file; do
        if [ -n "$file" ]; then
            ((count++))
            local basename=$(basename "$file")
            local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
            local age=$(get_file_age "$file")
            local validation=$(validate_backup "$file")
            local tf_version=$(jq -r '.terraform_version' "$file" 2>/dev/null || echo "unknown")
            
            printf "  %2d. %s\n" $count "$basename"
            printf "      Size: %-8s Age: %-8s Status: %s\n" "$(format_size $size)" "$age" "$validation"
            printf "      TF Version: %s\n" "$tf_version"
            echo ""
        fi
    done
}

# Function to show backup statistics
show_stats() {
    log_header "📊 Backup Statistics"
    echo "====================="
    
    local total_files=0
    local total_size=0
    
    for env in development staging production; do
        local files=$(ls "$BACKUP_DIR"/terraform-$env-*.tfstate 2>/dev/null || echo "")
        local env_count=0
        local env_size=0
        
        if [ -n "$files" ]; then
            while IFS= read -r file; do
                if [ -n "$file" ]; then
                    ((env_count++))
                    ((total_files++))
                    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
                    env_size=$((env_size + size))
                    total_size=$((total_size + size))
                fi
            done <<< "$files"
        fi
        
        printf "  %-12s: %2d backups, %s\n" "$env" "$env_count" "$(format_size $env_size)"
    done
    
    echo "  ----------------------------------------"
    printf "  %-12s: %2d backups, %s\n" "Total" "$total_files" "$(format_size $total_size)"
    
    # Show oldest and newest backups
    local oldest=$(ls -t "$BACKUP_DIR"/terraform-*.tfstate 2>/dev/null | tail -1)
    local newest=$(ls -t "$BACKUP_DIR"/terraform-*.tfstate 2>/dev/null | head -1)
    
    if [ -n "$oldest" ]; then
        echo ""
        echo "  Oldest backup: $(basename "$oldest") ($(get_file_age "$oldest"))"
    fi
    
    if [ -n "$newest" ]; then
        echo "  Newest backup: $(basename "$newest") ($(get_file_age "$newest"))"
    fi
    
    # Check backup index
    if [ -f "backups/index.json" ]; then
        local indexed_count=$(jq '.backups | length' backups/index.json 2>/dev/null || echo "0")
        echo "  Indexed backups: $indexed_count"
    fi
}

# Function to verify all backups
verify_backups() {
    log_header "🔍 Backup Verification"
    echo "======================"
    
    local total=0
    local valid=0
    local invalid=0
    local missing=0
    
    for env in development staging production; do
        local files=$(ls "$BACKUP_DIR"/terraform-$env-*.tfstate 2>/dev/null || echo "")
        
        if [ -n "$files" ]; then
            echo ""
            log_info "Verifying $env backups..."
            
            while IFS= read -r file; do
                if [ -n "$file" ]; then
                    ((total++))
                    local basename=$(basename "$file")
                    local status=$(validate_backup "$file")
                    
                    case $status in
                        OK*)
                            ((valid++))
                            echo "  ✅ $basename: $status"
                            ;;
                        INVALID)
                            ((invalid++))
                            echo "  ❌ $basename: $status"
                            ;;
                        MISSING)
                            ((missing++))
                            echo "  ⚠️  $basename: $status"
                            ;;
                    esac
                fi
            done <<< "$files"
        fi
    done
    
    echo ""
    echo "Verification Summary:"
    printf "  Valid:   %d/%d\n" $valid $total
    printf "  Invalid: %d/%d\n" $invalid $total
    printf "  Missing: %d/%d\n" $missing $total
    
    if [ $invalid -gt 0 ] || [ $missing -gt 0 ]; then
        log_warning "Some backups have issues and may need attention"
    else
        log_success "All backups are valid"
    fi
}

# Function to clean old backups
clean_backups() {
    log_header "🧹 Backup Cleanup"
    echo "=================="
    
    local keep_count=${KEEP_COUNT:-10}
    log_info "Keeping latest $keep_count backups per environment"
    
    local total_removed=0
    local total_space_saved=0
    
    for env in development staging production; do
        local files=$(ls -t "$BACKUP_DIR"/terraform-$env-*.tfstate 2>/dev/null || echo "")
        
        if [ -n "$files" ]; then
            local count=0
            local to_remove=""
            
            while IFS= read -r file; do
                if [ -n "$file" ]; then
                    ((count++))
                    if [ $count -gt $keep_count ]; then
                        to_remove="$to_remove $file"
                    fi
                fi
            done <<< "$files"
            
            if [ -n "$to_remove" ]; then
                local removed_count=0
                local space_saved=0
                
                for file in $to_remove; do
                    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
                    space_saved=$((space_saved + size))
                    rm -f "$file"
                    ((removed_count++))
                done
                
                total_removed=$((total_removed + removed_count))
                total_space_saved=$((total_space_saved + space_saved))
                
                log_success "Removed $removed_count old backups from $env (saved $(format_size $space_saved))"
            else
                log_info "No cleanup needed for $env ($(echo "$files" | wc -l | tr -d ' ') backups)"
            fi
        fi
    done
    
    if [ $total_removed -gt 0 ]; then
        echo ""
        log_success "Cleanup completed: removed $total_removed backups, saved $(format_size $total_space_saved)"
    else
        log_info "No cleanup needed"
    fi
}

# Main execution
case $ACTION in
    list)
        if [ "$ENVIRONMENT" = "all" ]; then
            for env in development staging production; do
                list_environment_backups $env
            done
        else
            list_environment_backups $ENVIRONMENT
        fi
        ;;
    stats)
        show_stats
        ;;
    verify)
        verify_backups
        ;;
    clean)
        clean_backups
        ;;
esac

# Show available actions
echo ""
log_info "Available actions:"
echo "  ./scripts/list-backups.sh [environment] list    - List backups"
echo "  ./scripts/list-backups.sh [environment] stats   - Show statistics"
echo "  ./scripts/list-backups.sh [environment] verify  - Verify backup integrity"
echo "  ./scripts/list-backups.sh [environment] clean   - Clean old backups"