#!/bin/bash
# Enhanced Alembic Migration Helper
# Provides additional safety checks and utilities for database migrations

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ALEMBIC_DIR="$PROJECT_ROOT/src"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
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

# Check if we're in the right directory
check_environment() {
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        log_error "Not in FastAPI project root directory"
        exit 1
    fi
    
    if [[ ! -d "$ALEMBIC_DIR/alembic" ]]; then
        log_error "Alembic directory not found at $ALEMBIC_DIR/alembic"
        exit 1
    fi
}

# Backup database before destructive operations
backup_database() {
    log_info "Creating database backup (if SQLite)..."
    
    if [[ -f "$PROJECT_ROOT/src/sqlite3.db" ]]; then
        BACKUP_FILE="$PROJECT_ROOT/src/sqlite3.db.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$PROJECT_ROOT/src/sqlite3.db" "$BACKUP_FILE"
        log_success "Database backed up to: $BACKUP_FILE"
    else
        log_info "No SQLite database found, skipping backup"
    fi
}

# Enhanced migration creation with validation
create_migration() {
    local message="$1"
    
    if [[ -z "$message" ]]; then
        log_error "Migration message is required"
        echo "Usage: $0 revision -m \"Your migration message\""
        exit 1
    fi
    
    log_info "Creating new migration: $message"
    
    cd "$ALEMBIC_DIR"
    
    # Generate migration
    alembic revision --autogenerate -m "$message"
    
    # Find the most recent migration file
    LATEST_MIGRATION=$(find alembic/versions -name "*.py" -type f -exec ls -t {} + | head -n1)
    
    if [[ -n "$LATEST_MIGRATION" ]]; then
        log_success "Migration created: $LATEST_MIGRATION"
        log_warning "🚨 IMPORTANT: Please review the migration file before applying!"
        log_info "Preview migration SQL with: $0 upgrade head --sql"
    fi
    
    cd - > /dev/null
}

# Safe upgrade with confirmation
safe_upgrade() {
    log_info "Preparing to upgrade database..."
    
    # Show current revision
    cd "$ALEMBIC_DIR"
    CURRENT_REV=$(alembic current 2>/dev/null | grep -o "[a-f0-9]\{12\}" || echo "none")
    TARGET_REV=$(alembic heads 2>/dev/null | grep -o "[a-f0-9]\{12\}" || echo "unknown")
    
    log_info "Current revision: $CURRENT_REV"
    log_info "Target revision: $TARGET_REV"
    
    if [[ "$CURRENT_REV" == "$TARGET_REV" ]]; then
        log_success "Database is already up to date"
        cd - > /dev/null
        return 0
    fi
    
    # Show pending migrations
    log_info "Pending migrations:"
    alembic history -r "$CURRENT_REV:$TARGET_REV" 2>/dev/null || true
    
    # Backup before upgrade
    backup_database
    
    # Apply migrations
    log_info "Applying migrations..."
    alembic upgrade head
    
    log_success "Database upgrade completed successfully"
    cd - > /dev/null
}

# Show migration status
show_status() {
    cd "$ALEMBIC_DIR"
    
    log_info "Database Migration Status"
    echo "========================="
    
    echo -e "\n${BLUE}Current Revision:${NC}"
    alembic current || log_error "Failed to get current revision"
    
    echo -e "\n${BLUE}Available Heads:${NC}"
    alembic heads || log_error "Failed to get heads"
    
    echo -e "\n${BLUE}Migration History (last 5):${NC}"
    alembic history -r -5: || log_error "Failed to get history"
    
    cd - > /dev/null
}

# Main command dispatcher
main() {
    check_environment
    
    case "${1:-help}" in
        "revision"|"rev")
            shift
            create_migration "$@"
            ;;
        "upgrade"|"up")
            shift
            if [[ "$1" == "--safe" ]]; then
                safe_upgrade
            else
                cd "$ALEMBIC_DIR"
                alembic upgrade "$@"
                cd - > /dev/null
            fi
            ;;
        "downgrade"|"down")
            shift
            log_warning "Downgrade operation - creating backup first"
            backup_database
            cd "$ALEMBIC_DIR"
            alembic downgrade "$@"
            cd - > /dev/null
            ;;
        "status"|"current")
            show_status
            ;;
        "history")
            cd "$ALEMBIC_DIR"
            alembic history "$@"
            cd - > /dev/null
            ;;
        "help"|"-h"|"--help")
            echo "Enhanced Alembic Migration Helper"
            echo ""
            echo "Usage: $0 <command> [options]"
            echo ""
            echo "Commands:"
            echo "  revision -m \"message\"    Create new migration"
            echo "  upgrade [--safe]          Apply pending migrations"
            echo "  downgrade <target>        Rollback to target revision"
            echo "  status                    Show migration status"
            echo "  history                   Show migration history"
            echo "  help                      Show this help"
            echo ""
            echo "Examples:"
            echo "  $0 revision -m \"Add user table\""
            echo "  $0 upgrade --safe"
            echo "  $0 status"
            ;;
        *)
            # Pass through to alembic for other commands
            cd "$ALEMBIC_DIR"
            alembic "$@"
            cd - > /dev/null
            ;;
    esac
}

main "$@"
