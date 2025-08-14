# US004: Notification Persistence & History

## 📊 Story Information
- **Epic**: Event Notification System
- **Priority**: P1 (High)
- **Story Points**: 5
- **Sprint**: Real-time Sprint 2
- **Feature Flag**: `enable_notification_history`
- **Dependencies**: US001 (Backend Foundation), US002 (Frontend Bell)
- **Assignee**: Backend Developer

## 👤 User Story
**As a** coaching platform user  
**I want** to view my complete notification history and manage old notifications  
**So that** I can review past events and keep my notification list organized

### Business Value
- **User Control**: Users can manage their notification inbox like email
- **Audit Trail**: Complete history of system events for troubleshooting
- **Performance**: Efficient storage and retrieval of large notification volumes
- **Data Retention**: Compliance with data retention policies

## ✅ Acceptance Criteria

### AC1: Complete Notification History
**Given** I have accumulated many notifications over time  
**When** I access my notification history  
**Then** I can view all notifications with pagination and filtering

**History Requirements:**
- Paginated list of all notifications (20 per page)
- Filter by type (success, error, info, warning)
- Filter by status (read, unread, archived)
- Filter by date range
- Sort by created date (newest first by default)

### AC2: Notification Archival
**Given** I have read notifications that I no longer need  
**When** I archive them  
**Then** they are hidden from my main notification list but remain searchable

**Archival Requirements:**
- Individual notification archival
- Bulk archive operations (all read, all older than X days)
- Archived notifications excluded from unread count
- Archive/unarchive reversible operations

### AC3: Automatic Data Cleanup
**Given** the system has accumulated old notifications  
**When** notifications are older than the retention period  
**Then** they are automatically soft-deleted to maintain performance

**Cleanup Requirements:**
- Soft delete notifications older than 90 days
- Hard delete soft-deleted notifications older than 1 year
- Configurable retention periods per notification type
- Batch cleanup processes run daily

### AC4: Search and Export
**Given** I need to find specific notifications  
**When** I search my notification history  
**Then** I can find notifications by content and export results

**Search Requirements:**
- Full-text search in title and message
- Search by session ID or related entities
- Export search results as CSV/JSON
- Search across archived notifications

### AC5: Performance Optimization
**Given** the system has millions of notifications  
**When** users access their notification history  
**Then** queries complete in <100ms with proper indexing and caching

## 🧪 TDD Test Implementation

### Backend Persistence Tests (Required: 5 tests)

```python
# Test 1: Pagination (Write First)
def test_should_paginate_notification_history():
    """RED: Pagination not implemented"""
    user_id = uuid4()
    
    # Create 25 notifications
    for i in range(25):
        create_notification(user_id, f"Title {i}", "Message", NotificationType.INFO)
    
    # Test first page
    page1 = get_notification_history(user_id, page=1, limit=10)
    assert len(page1.notifications) == 10
    assert page1.total == 25
    assert page1.page == 1
    assert page1.pages == 3
    
    # Test second page
    page2 = get_notification_history(user_id, page=2, limit=10)
    assert len(page2.notifications) == 10
    assert page2.page == 2
    
    # Ensure different results
    page1_ids = {n.id for n in page1.notifications}
    page2_ids = {n.id for n in page2.notifications}
    assert page1_ids.isdisjoint(page2_ids)

# Test 2: Filtering (Write Second)
def test_should_filter_notifications_by_type_and_status():
    """RED: Filtering not implemented"""
    user_id = uuid4()
    
    create_notification(user_id, "Success", "Message", NotificationType.SUCCESS, NotificationStatus.READ)
    create_notification(user_id, "Error", "Message", NotificationType.ERROR, NotificationStatus.UNREAD)
    create_notification(user_id, "Info", "Message", NotificationType.INFO, NotificationStatus.ARCHIVED)
    
    # Filter by type
    success_notifications = get_notification_history(
        user_id, 
        filters={"type": NotificationType.SUCCESS}
    )
    assert len(success_notifications.notifications) == 1
    assert success_notifications.notifications[0].type == NotificationType.SUCCESS
    
    # Filter by status
    unread_notifications = get_notification_history(
        user_id,
        filters={"status": NotificationStatus.UNREAD}
    )
    assert len(unread_notifications.notifications) == 1
    assert unread_notifications.notifications[0].status == NotificationStatus.UNREAD
    
    # Combined filters
    error_unread = get_notification_history(
        user_id,
        filters={
            "type": NotificationType.ERROR,
            "status": NotificationStatus.UNREAD
        }
    )
    assert len(error_unread.notifications) == 1

# Test 3: Archival Operations (Write Third)
def test_should_archive_and_unarchive_notifications():
    """RED: Archival operations not implemented"""
    user_id = uuid4()
    
    notification = create_notification(user_id, "Test", "Message", NotificationType.INFO)
    assert notification.status != NotificationStatus.ARCHIVED
    
    # Archive notification
    archive_notification(notification.id)
    
    updated_notification = get_notification_by_id(notification.id)
    assert updated_notification.status == NotificationStatus.ARCHIVED
    
    # Archived notifications shouldn't appear in main list
    main_list = get_notifications(user_id)
    assert notification.id not in [n.id for n in main_list]
    
    # But should appear in archived list
    archived_list = get_notification_history(user_id, filters={"status": NotificationStatus.ARCHIVED})
    assert notification.id in [n.id for n in archived_list.notifications]
    
    # Unarchive should restore
    unarchive_notification(notification.id)
    restored = get_notification_by_id(notification.id)
    assert restored.status == NotificationStatus.READ

# Test 4: Bulk Operations (Write Fourth)
def test_should_perform_bulk_archive_operations():
    """RED: Bulk operations not implemented"""
    user_id = uuid4()
    
    # Create mix of read and unread notifications
    read_notifications = []
    unread_notifications = []
    
    for i in range(5):
        read_notif = create_notification(user_id, f"Read {i}", "Message", NotificationType.INFO)
        mark_notification_as_read(read_notif.id)
        read_notifications.append(read_notif)
        
        unread_notif = create_notification(user_id, f"Unread {i}", "Message", NotificationType.INFO)
        unread_notifications.append(unread_notif)
    
    # Bulk archive all read notifications
    result = bulk_archive_notifications(user_id, criteria={"status": "read"})
    assert result.archived_count == 5
    
    # Verify only read notifications were archived
    for notif in read_notifications:
        updated = get_notification_by_id(notif.id)
        assert updated.status == NotificationStatus.ARCHIVED
    
    for notif in unread_notifications:
        updated = get_notification_by_id(notif.id)
        assert updated.status == NotificationStatus.UNREAD

# Test 5: Automatic Cleanup (Write Fifth)
def test_should_automatically_cleanup_old_notifications():
    """RED: Cleanup process not implemented"""
    user_id = uuid4()
    
    # Create old notifications (simulate by setting created_at)
    old_date = datetime.utcnow() - timedelta(days=95)  # Older than 90 days
    recent_date = datetime.utcnow() - timedelta(days=30)  # Recent
    
    old_notification = create_notification(user_id, "Old", "Message", NotificationType.INFO)
    # Simulate old creation date
    db.execute(
        update(Notification)
        .where(Notification.id == old_notification.id)
        .values(created_at=old_date)
    )
    
    recent_notification = create_notification(user_id, "Recent", "Message", NotificationType.INFO)
    
    # Run cleanup process
    cleanup_result = run_notification_cleanup()
    
    # Old notification should be soft deleted
    old_updated = get_notification_by_id(old_notification.id, include_deleted=True)
    assert old_updated.deleted_at is not None
    
    # Recent notification should remain
    recent_updated = get_notification_by_id(recent_notification.id)
    assert recent_updated.deleted_at is None
    
    # Verify cleanup stats
    assert cleanup_result.soft_deleted_count >= 1
```

### Frontend History Tests (Required: 3 tests)

```typescript
// Test 1: History View (Write First)
describe('NotificationHistory', () => {
  it('should display paginated notification history', async () => {
    // RED: History view not implemented
    const mockHistory = {
      notifications: [
        { id: '1', title: 'Test 1', created_at: '2025-01-01T10:00:00Z', status: 'read' },
        { id: '2', title: 'Test 2', created_at: '2025-01-01T09:00:00Z', status: 'unread' }
      ],
      total: 25,
      page: 1,
      pages: 3
    };
    
    render(<NotificationHistory history={mockHistory} />);
    
    expect(screen.getByText('Test 1')).toBeInTheDocument();
    expect(screen.getByText('Test 2')).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    expect(screen.getByText('25 total notifications')).toBeInTheDocument();
  });

  // Test 2: Filtering Interface (Write Second)
  it('should provide filtering controls', async () => {
    // RED: Filter controls not implemented
    const mockOnFilter = jest.fn();
    
    render(<NotificationHistory onFilter={mockOnFilter} />);
    
    // Type filter
    const typeSelect = screen.getByLabelText('Filter by type');
    await userEvent.selectOptions(typeSelect, 'success');
    
    expect(mockOnFilter).toHaveBeenCalledWith({
      type: 'success'
    });
    
    // Status filter
    const statusSelect = screen.getByLabelText('Filter by status');
    await userEvent.selectOptions(statusSelect, 'archived');
    
    expect(mockOnFilter).toHaveBeenCalledWith({
      type: 'success',
      status: 'archived'
    });
  });

  // Test 3: Bulk Operations (Write Third)
  it('should support bulk archive operations', async () => {
    // RED: Bulk operations not implemented
    const mockBulkArchive = jest.fn();
    const mockNotifications = [
      { id: '1', status: 'read', selected: true },
      { id: '2', status: 'read', selected: true },
      { id: '3', status: 'unread', selected: false }
    ];
    
    render(
      <NotificationHistory 
        notifications={mockNotifications}
        onBulkArchive={mockBulkArchive}
      />
    );
    
    const archiveButton = screen.getByText('Archive Selected');
    await userEvent.click(archiveButton);
    
    expect(mockBulkArchive).toHaveBeenCalledWith(['1', '2']);
  });
});
```

## 🛠️ Technical Implementation

### Database Schema Enhancements

```sql
-- Add indexes for history queries
CREATE INDEX idx_notifications_user_created_desc ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_user_type ON notifications(user_id, type);
CREATE INDEX idx_notifications_user_status ON notifications(user_id, status);
CREATE INDEX idx_notifications_full_text ON notifications USING gin(to_tsvector('english', title || ' ' || message));

-- Add soft delete fields
ALTER TABLE notifications ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE notifications ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE;

-- Partial index for active notifications (performance optimization)
CREATE INDEX idx_notifications_active ON notifications(user_id, created_at DESC) WHERE deleted_at IS NULL;
```

### Backend API Enhancements

```python
# Enhanced notification history endpoint
@router.get("/notifications/history")
async def get_notification_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type_filter: Optional[str] = Query(None, alias="type"),
    status_filter: Optional[str] = Query(None, alias="status"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> NotificationHistoryResponse:
    """Get paginated notification history with filtering"""
    
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.deleted_at.is_(None)  # Exclude soft deleted
    )
    
    # Apply filters
    if type_filter:
        query = query.filter(Notification.type == type_filter)
    
    if status_filter:
        if status_filter == "archived":
            query = query.filter(Notification.status == NotificationStatus.ARCHIVED)
        elif status_filter == "unread":
            query = query.filter(Notification.status == NotificationStatus.UNREAD)
        elif status_filter == "read":
            query = query.filter(Notification.status == NotificationStatus.READ)
    
    if not include_archived and status_filter != "archived":
        query = query.filter(Notification.status != NotificationStatus.ARCHIVED)
    
    if date_from:
        query = query.filter(Notification.created_at >= date_from)
    
    if date_to:
        query = query.filter(Notification.created_at <= date_to)
    
    if search:
        query = query.filter(
            or_(
                Notification.title.ilike(f"%{search}%"),
                Notification.message.ilike(f"%{search}%")
            )
        )
    
    # Count total before pagination
    total = query.count()
    
    # Apply pagination and ordering
    notifications = query.order_by(Notification.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()
    
    return NotificationHistoryResponse(
        notifications=[NotificationResponse.from_notification(n) for n in notifications],
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit)
    )

# Bulk archive endpoint
@router.patch("/notifications/bulk-archive")
async def bulk_archive_notifications(
    request: BulkArchiveRequest,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> BulkOperationResponse:
    """Archive multiple notifications"""
    
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.deleted_at.is_(None)
    )
    
    if request.notification_ids:
        query = query.filter(Notification.id.in_(request.notification_ids))
    
    if request.criteria:
        if request.criteria.get("status") == "read":
            query = query.filter(Notification.status == NotificationStatus.READ)
        if request.criteria.get("older_than_days"):
            cutoff_date = datetime.utcnow() - timedelta(days=request.criteria["older_than_days"])
            query = query.filter(Notification.created_at < cutoff_date)
    
    # Update to archived status
    updated_count = query.update({
        "status": NotificationStatus.ARCHIVED,
        "archived_at": datetime.utcnow()
    }, synchronize_session=False)
    
    db.commit()
    
    return BulkOperationResponse(
        archived_count=updated_count,
        message=f"Archived {updated_count} notifications"
    )
```

### Cleanup Background Task

```python
# Celery task for notification cleanup
@celery_app.task
def cleanup_old_notifications():
    """Daily cleanup task for old notifications"""
    
    with get_db_session() as db:
        now = datetime.utcnow()
        soft_delete_cutoff = now - timedelta(days=90)  # Configurable
        hard_delete_cutoff = now - timedelta(days=365)  # 1 year
        
        # Soft delete old notifications
        soft_delete_count = db.query(Notification).filter(
            Notification.created_at < soft_delete_cutoff,
            Notification.deleted_at.is_(None)
        ).update({
            "deleted_at": now
        }, synchronize_session=False)
        
        # Hard delete very old soft-deleted notifications
        hard_delete_count = db.query(Notification).filter(
            Notification.deleted_at < hard_delete_cutoff
        ).delete(synchronize_session=False)
        
        db.commit()
        
        logger.info(
            f"Notification cleanup completed: "
            f"soft_deleted={soft_delete_count}, hard_deleted={hard_delete_count}"
        )
        
        return {
            "soft_deleted_count": soft_delete_count,
            "hard_deleted_count": hard_delete_count
        }

# Schedule daily cleanup
from celery.schedules import crontab
celery_app.conf.beat_schedule = {
    'cleanup-notifications': {
        'task': 'cleanup_old_notifications',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
}
```

## 📊 Definition of Done Checklist

### Testing Requirements
- [ ] **Backend persistence tests**: 5/5 tests using TDD methodology
- [ ] **Frontend history tests**: 3/3 tests covering UI interactions
- [ ] **Bulk operation tests**: Archive/unarchive operations tested
- [ ] **Cleanup task tests**: Automatic data retention verified
- [ ] **Performance tests**: Large dataset queries <100ms

### Code Quality Requirements
- [ ] **Database optimization**: Proper indexing for history queries
- [ ] **Memory efficiency**: Pagination prevents large result sets
- [ ] **Error handling**: Graceful handling of bulk operation failures
- [ ] **Code review**: Database and API changes reviewed
- [ ] **Migration tested**: Schema changes applied and rolled back

### Performance Requirements
- [ ] **Query optimization**: History queries complete in <100ms
- [ ] **Index usage**: Database query plans verified
- [ ] **Pagination efficiency**: Large datasets handled properly
- [ ] **Cleanup performance**: Background tasks don't impact user queries
- [ ] **Memory usage**: Bulk operations don't cause memory spikes

### Data Management Requirements
- [ ] **Retention compliance**: Data automatically cleaned per policy
- [ ] **Soft delete safety**: Accidental deletes can be recovered
- [ ] **Archive functionality**: Users can organize their notifications
- [ ] **Search capability**: Users can find historical notifications
- [ ] **Export functionality**: Data can be exported for compliance

## 🚀 Implementation Notes

### Performance Considerations
- **Database partitioning**: Consider partitioning by created_at for very large datasets
- **Read replicas**: Use read replicas for history queries to reduce main DB load
- **Caching**: Cache commonly accessed notification counts and summaries
- **Batch processing**: Process cleanup operations in batches to avoid locks

### Data Retention Strategy
- **Configurable periods**: Different retention for different notification types
- **Compliance friendly**: Support GDPR "right to be forgotten" requests
- **Audit trail**: Log all cleanup operations for compliance
- **Recovery process**: Soft deletes allow recovery within reasonable timeframe

---

**🔄 Next Story**: [US005: Notification Preferences & Settings](US005-notification-preferences-settings.md)  
**⬅️ Previous Story**: [US003: SSE Real-time Updates](US003-sse-real-time-updates.md)  
**📋 Back to**: [Feature Overview](README.md)