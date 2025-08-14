# US005: Notification Preferences & Settings

## 📊 Story Information
- **Epic**: Event Notification System
- **Priority**: P2 (Medium)
- **Story Points**: 4
- **Sprint**: User Experience Sprint 3
- **Feature Flag**: `enable_notification_preferences`
- **Dependencies**: US001 (Backend Foundation), US002 (Frontend Bell)
- **Assignee**: Full-stack Developer

## 👤 User Story
**As a** coaching platform user  
**I want** to control which notifications I receive and how I receive them  
**So that** I only get relevant notifications in my preferred format

### Business Value
- **User Control**: Reduces notification fatigue and improves experience
- **Engagement**: Users more likely to engage with relevant notifications
- **Retention**: Customizable experience increases user satisfaction
- **Reduced Unsubscribes**: Users can tune notifications instead of turning them off

## ✅ Acceptance Criteria

### AC1: Notification Type Preferences
**Given** I want to control which types of notifications I receive  
**When** I access my notification settings  
**Then** I can enable/disable each notification type

**Type Controls:**
- Transcription completed (success notifications)
- Transcription failed (error notifications)
- System maintenance (info notifications)
- Account updates (warning notifications)
- Weekly summary emails

### AC2: Delivery Channel Preferences
**Given** I want to choose how notifications are delivered  
**When** I configure my delivery preferences  
**Then** I can select from multiple channels for each type

**Delivery Channels:**
- In-app notifications (dashboard bell)
- Browser push notifications
- Email notifications
- SMS notifications (future)
- Digest emails (daily/weekly summaries)

### AC3: Quiet Hours Configuration
**Given** I don't want notifications during certain hours  
**When** I set quiet hours  
**Then** notifications are queued and delivered when quiet hours end

**Quiet Hours Features:**
- Start and end time configuration
- Timezone awareness
- Emergency override for critical failures
- Weekend/weekday different schedules

### AC4: Frequency Controls
**Given** I receive many notifications of the same type  
**When** I configure frequency limits  
**Then** similar notifications are batched or limited

**Frequency Options:**
- Immediate delivery
- Batched every 15 minutes
- Batched hourly
- Daily digest only
- Weekly digest only

### AC5: Quick Settings Access
**Given** I want to quickly adjust notification settings  
**When** I click on a notification or use the bell dropdown  
**Then** I can access quick settings without leaving the current page

## 🧪 TDD Test Implementation

### Backend Preferences Tests (Required: 4 tests)

```python
# Test 1: Preference Storage (Write First)
def test_should_store_user_notification_preferences():
    """RED: Preference model doesn't exist yet"""
    user_id = uuid4()
    
    preferences = NotificationPreferences(
        user_id=user_id,
        transcription_complete=True,
        transcription_failed=True,
        system_maintenance=False,
        email_notifications=True,
        browser_notifications=False,
        quiet_hours_start="22:00",
        quiet_hours_end="08:00",
        timezone="America/New_York"
    )
    
    saved_prefs = save_notification_preferences(preferences)
    assert saved_prefs.id is not None
    assert saved_prefs.user_id == user_id
    assert saved_prefs.transcription_complete == True
    assert saved_prefs.system_maintenance == False

# Test 2: Preference Filtering (Write Second)
def test_should_filter_notifications_by_user_preferences():
    """RED: Preference filtering not implemented"""
    user_id = uuid4()
    
    # User disables system maintenance notifications
    set_notification_preference(user_id, "system_maintenance", False)
    set_notification_preference(user_id, "transcription_complete", True)
    
    # Create notifications of different types
    maintenance_notif = create_notification(
        user_id, "Maintenance", "System update", NotificationType.INFO
    )
    
    transcription_notif = create_notification(
        user_id, "Transcription Complete", "Ready", NotificationType.SUCCESS
    )
    
    # Should filter based on preferences
    delivered_notifications = get_deliverable_notifications(user_id)
    
    notif_titles = [n.title for n in delivered_notifications]
    assert "Transcription Complete" in notif_titles
    assert "Maintenance" not in notif_titles

# Test 3: Quiet Hours (Write Third)
def test_should_respect_quiet_hours_settings():
    """RED: Quiet hours logic not implemented"""
    user_id = uuid4()
    
    # Set quiet hours 10 PM to 8 AM
    set_quiet_hours(user_id, start_time="22:00", end_time="08:00", timezone="UTC")
    
    # Simulate current time during quiet hours (2 AM UTC)
    with freeze_time("2025-01-01 02:00:00"):
        notification = create_notification(
            user_id, "Test", "Message", NotificationType.INFO
        )
        
        # Should be queued, not delivered immediately
        delivery_status = get_notification_delivery_status(notification.id)
        assert delivery_status.status == "queued"
        assert delivery_status.scheduled_for is not None
        
    # Simulate time after quiet hours (9 AM UTC)
    with freeze_time("2025-01-01 09:00:00"):
        # Should now be deliverable
        process_queued_notifications()
        
        updated_status = get_notification_delivery_status(notification.id)
        assert updated_status.status == "delivered"

# Test 4: Frequency Batching (Write Fourth)
def test_should_batch_notifications_by_frequency_setting():
    """RED: Frequency batching not implemented"""
    user_id = uuid4()
    
    # Set user preference to batch notifications every 15 minutes
    set_notification_frequency(user_id, NotificationType.SUCCESS, "batch_15min")
    
    # Create multiple notifications quickly
    notification1 = create_notification(user_id, "Complete 1", "Message", NotificationType.SUCCESS)
    notification2 = create_notification(user_id, "Complete 2", "Message", NotificationType.SUCCESS)
    notification3 = create_notification(user_id, "Complete 3", "Message", NotificationType.SUCCESS)
    
    # Should be batched together
    delivery_plan = get_notification_delivery_plan(user_id)
    
    # All notifications should be in the same batch
    batch_groups = group_by_delivery_time(delivery_plan)
    success_batches = [b for b in batch_groups if b.notification_type == NotificationType.SUCCESS]
    
    assert len(success_batches) == 1
    assert len(success_batches[0].notifications) == 3
```

### Frontend Settings Tests (Required: 3 tests)

```typescript
// Test 1: Settings Panel (Write First)
describe('NotificationSettings', () => {
  it('should render notification preference controls', () => {
    // RED: Settings component doesn't exist
    const mockPreferences = {
      transcription_complete: true,
      transcription_failed: true,
      system_maintenance: false,
      email_notifications: true,
      browser_notifications: false
    };
    
    render(<NotificationSettings preferences={mockPreferences} />);
    
    expect(screen.getByLabelText('Transcription completed')).toBeChecked();
    expect(screen.getByLabelText('System maintenance')).not.toBeChecked();
    expect(screen.getByLabelText('Email notifications')).toBeChecked();
    expect(screen.getByLabelText('Browser notifications')).not.toBeChecked();
  });

  // Test 2: Preference Updates (Write Second)
  it('should update preferences when toggles changed', async () => {
    // RED: Update functionality not implemented
    const mockOnUpdate = jest.fn();
    const mockPreferences = {
      transcription_complete: true,
      system_maintenance: false
    };
    
    render(
      <NotificationSettings 
        preferences={mockPreferences}
        onUpdate={mockOnUpdate}
      />
    );
    
    const maintenanceToggle = screen.getByLabelText('System maintenance');
    await userEvent.click(maintenanceToggle);
    
    expect(mockOnUpdate).toHaveBeenCalledWith({
      ...mockPreferences,
      system_maintenance: true
    });
  });

  // Test 3: Quiet Hours Configuration (Write Third)
  it('should configure quiet hours with timezone', async () => {
    // RED: Quiet hours UI not implemented
    const mockOnQuietHoursUpdate = jest.fn();
    
    render(
      <NotificationSettings 
        onQuietHoursUpdate={mockOnQuietHoursUpdate}
      />
    );
    
    // Set start time
    const startTimeInput = screen.getByLabelText('Quiet hours start');
    await userEvent.clear(startTimeInput);
    await userEvent.type(startTimeInput, '22:00');
    
    // Set end time
    const endTimeInput = screen.getByLabelText('Quiet hours end');
    await userEvent.clear(endTimeInput);
    await userEvent.type(endTimeInput, '08:00');
    
    // Select timezone
    const timezoneSelect = screen.getByLabelText('Timezone');
    await userEvent.selectOptions(timezoneSelect, 'America/New_York');
    
    const saveButton = screen.getByText('Save Quiet Hours');
    await userEvent.click(saveButton);
    
    expect(mockOnQuietHoursUpdate).toHaveBeenCalledWith({
      start_time: '22:00',
      end_time: '08:00',
      timezone: 'America/New_York'
    });
  });
});
```

## 🛠️ Technical Implementation

### Database Schema

```sql
-- User notification preferences table
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification type preferences
    transcription_complete BOOLEAN DEFAULT true,
    transcription_failed BOOLEAN DEFAULT true,
    system_maintenance BOOLEAN DEFAULT true,
    account_updates BOOLEAN DEFAULT true,
    weekly_summary BOOLEAN DEFAULT true,
    
    -- Delivery channel preferences
    in_app_notifications BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT true,
    browser_notifications BOOLEAN DEFAULT false,
    sms_notifications BOOLEAN DEFAULT false,
    
    -- Quiet hours settings
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME DEFAULT '22:00:00',
    quiet_hours_end TIME DEFAULT '08:00:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    quiet_hours_weekends BOOLEAN DEFAULT true,
    
    -- Frequency settings (JSON for flexibility)
    frequency_settings JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_user_preferences UNIQUE (user_id)
);

CREATE INDEX idx_notification_preferences_user_id ON notification_preferences(user_id);

-- Notification delivery queue for batching and quiet hours
CREATE TABLE notification_delivery_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delivery_channel delivery_channel_type NOT NULL,
    scheduled_for TIMESTAMP WITH TIME ZONE NOT NULL,
    status delivery_status DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enums
CREATE TYPE delivery_channel_type AS ENUM ('in_app', 'email', 'browser_push', 'sms');
CREATE TYPE delivery_status AS ENUM ('pending', 'delivered', 'failed', 'cancelled');

CREATE INDEX idx_delivery_queue_scheduled ON notification_delivery_queue(scheduled_for) WHERE status = 'pending';
CREATE INDEX idx_delivery_queue_user_channel ON notification_delivery_queue(user_id, delivery_channel);
```

### Backend API Endpoints

```python
# Notification preferences API
@router.get("/notifications/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> NotificationPreferencesResponse:
    """Get user's notification preferences"""
    
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreferences(
            user_id=current_user.id,
            transcription_complete=True,
            transcription_failed=True,
            system_maintenance=True,
            account_updates=True,
            email_notifications=True,
            in_app_notifications=True
        )
        db.add(preferences)
        db.commit()
    
    return NotificationPreferencesResponse.from_model(preferences)

@router.patch("/notifications/preferences")
async def update_notification_preferences(
    updates: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> NotificationPreferencesResponse:
    """Update user's notification preferences"""
    
    preferences = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not preferences:
        preferences = NotificationPreferences(user_id=current_user.id)
        db.add(preferences)
    
    # Update only provided fields
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    preferences.updated_at = datetime.utcnow()
    db.commit()
    
    return NotificationPreferencesResponse.from_model(preferences)

# Delivery scheduling service
class NotificationDeliveryService:
    def __init__(self, db: Session):
        self.db = db
    
    async def schedule_notification(self, notification: Notification) -> List[DeliveryQueueItem]:
        """Schedule notification delivery based on user preferences"""
        
        preferences = self.db.query(NotificationPreferences).filter(
            NotificationPreferences.user_id == notification.user_id
        ).first()
        
        if not preferences:
            preferences = self._get_default_preferences(notification.user_id)
        
        delivery_items = []
        
        # Check if notification type is enabled
        if not self._is_notification_type_enabled(notification.type, preferences):
            return delivery_items
        
        # Schedule for each enabled delivery channel
        if preferences.in_app_notifications:
            delivery_items.append(self._schedule_in_app(notification, preferences))
        
        if preferences.email_notifications:
            delivery_items.append(self._schedule_email(notification, preferences))
        
        if preferences.browser_notifications:
            delivery_items.append(self._schedule_browser_push(notification, preferences))
        
        # Add to delivery queue
        for item in delivery_items:
            self.db.add(item)
        
        self.db.commit()
        return delivery_items
    
    def _schedule_in_app(self, notification: Notification, preferences: NotificationPreferences) -> DeliveryQueueItem:
        """Schedule in-app notification with frequency batching and quiet hours"""
        
        scheduled_time = self._calculate_delivery_time(
            notification.type,
            preferences,
            DeliveryChannelType.IN_APP
        )
        
        return DeliveryQueueItem(
            notification_id=notification.id,
            user_id=notification.user_id,
            delivery_channel=DeliveryChannelType.IN_APP,
            scheduled_for=scheduled_time
        )
    
    def _calculate_delivery_time(self, notification_type: NotificationType, preferences: NotificationPreferences, channel: DeliveryChannelType) -> datetime:
        """Calculate when notification should be delivered based on preferences"""
        
        base_time = datetime.utcnow()
        
        # Apply frequency batching
        frequency_settings = preferences.frequency_settings or {}
        frequency = frequency_settings.get(f"{notification_type}_{channel}", "immediate")
        
        if frequency == "batch_15min":
            # Round up to next 15-minute interval
            minutes = base_time.minute
            next_interval = ((minutes // 15) + 1) * 15
            if next_interval >= 60:
                base_time = base_time.replace(hour=base_time.hour + 1, minute=0)
            else:
                base_time = base_time.replace(minute=next_interval)
        elif frequency == "batch_hourly":
            base_time = base_time.replace(minute=0) + timedelta(hours=1)
        elif frequency == "daily_digest":
            base_time = base_time.replace(hour=9, minute=0) + timedelta(days=1)
        
        # Apply quiet hours
        if preferences.quiet_hours_enabled:
            base_time = self._apply_quiet_hours(base_time, preferences)
        
        return base_time
    
    def _apply_quiet_hours(self, scheduled_time: datetime, preferences: NotificationPreferences) -> datetime:
        """Adjust delivery time to respect quiet hours"""
        
        user_tz = pytz.timezone(preferences.timezone)
        local_time = scheduled_time.astimezone(user_tz)
        
        quiet_start = preferences.quiet_hours_start
        quiet_end = preferences.quiet_hours_end
        
        # Check if current time is in quiet hours
        current_time = local_time.time()
        
        if self._is_in_quiet_hours(current_time, quiet_start, quiet_end):
            # Schedule for end of quiet hours
            next_day = local_time.date()
            if quiet_end < quiet_start:  # Quiet hours cross midnight
                if current_time >= quiet_start:
                    next_day += timedelta(days=1)
            
            end_of_quiet = datetime.combine(next_day, quiet_end, user_tz)
            return end_of_quiet.astimezone(pytz.UTC)
        
        return scheduled_time
```

### Frontend Settings Component

```typescript
// components/notifications/NotificationSettings.tsx
import { useState, useEffect } from 'react';
import { Switch, Select, TimePicker } from '@/components/ui';

interface NotificationSettingsProps {
  preferences?: NotificationPreferences;
  onUpdate?: (preferences: Partial<NotificationPreferences>) => void;
}

export const NotificationSettings: React.FC<NotificationSettingsProps> = ({
  preferences,
  onUpdate
}) => {
  const [localPreferences, setLocalPreferences] = useState(preferences || {});
  const [isLoading, setIsLoading] = useState(false);
  
  const handleToggle = async (key: keyof NotificationPreferences, value: boolean) => {
    const updated = { ...localPreferences, [key]: value };
    setLocalPreferences(updated);
    
    try {
      setIsLoading(true);
      await onUpdate?.(updated);
    } catch (error) {
      console.error('Failed to update preferences:', error);
      // Revert on error
      setLocalPreferences(localPreferences);
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium mb-4">Notification Types</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Transcription completed</label>
            <Switch
              checked={localPreferences.transcription_complete}
              onChange={(checked) => handleToggle('transcription_complete', checked)}
              disabled={isLoading}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Transcription failed</label>
            <Switch
              checked={localPreferences.transcription_failed}
              onChange={(checked) => handleToggle('transcription_failed', checked)}
              disabled={isLoading}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">System maintenance</label>
            <Switch
              checked={localPreferences.system_maintenance}
              onChange={(checked) => handleToggle('system_maintenance', checked)}
              disabled={isLoading}
            />
          </div>
        </div>
      </div>
      
      <div>
        <h3 className="text-lg font-medium mb-4">Delivery Channels</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">In-app notifications</label>
            <Switch
              checked={localPreferences.in_app_notifications}
              onChange={(checked) => handleToggle('in_app_notifications', checked)}
              disabled={isLoading}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Email notifications</label>
            <Switch
              checked={localPreferences.email_notifications}
              onChange={(checked) => handleToggle('email_notifications', checked)}
              disabled={isLoading}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Browser notifications</label>
            <Switch
              checked={localPreferences.browser_notifications}
              onChange={(checked) => handleToggle('browser_notifications', checked)}
              disabled={isLoading}
            />
          </div>
        </div>
      </div>
      
      <QuietHoursSettings
        preferences={localPreferences}
        onUpdate={onUpdate}
        disabled={isLoading}
      />
      
      <FrequencySettings
        preferences={localPreferences}
        onUpdate={onUpdate}
        disabled={isLoading}
      />
    </div>
  );
};
```

## 📊 Definition of Done Checklist

### Testing Requirements
- [ ] **Backend preference tests**: 4/4 tests using TDD methodology
- [ ] **Frontend settings tests**: 3/3 tests covering UI interactions
- [ ] **Integration tests**: End-to-end preference flow tested
- [ ] **Quiet hours tests**: Timezone and scheduling logic verified
- [ ] **Frequency batching tests**: Notification batching working properly

### Code Quality Requirements
- [ ] **Database migration**: Preference schema created and tested
- [ ] **Default preferences**: New users get sensible defaults
- [ ] **Preference validation**: Invalid settings rejected gracefully
- [ ] **Error handling**: Failed preference updates handled gracefully
- [ ] **Performance**: Preference queries optimized with proper indexing

### User Experience Requirements
- [ ] **Settings accessibility**: Settings panel fully accessible via keyboard
- [ ] **Real-time feedback**: Changes saved immediately with loading states
- [ ] **Clear explanations**: Each setting has helpful description
- [ ] **Quick access**: Settings reachable from notification bell
- [ ] **Responsive design**: Settings work on mobile and desktop

### Integration Requirements
- [ ] **Notification filtering**: Preferences properly filter notifications
- [ ] **Delivery scheduling**: Quiet hours and batching working
- [ ] **SSE integration**: Real-time delivery respects preferences
- [ ] **Email integration**: Email preferences control email delivery
- [ ] **Browser push**: Browser notification permissions integrated

---

**🔄 Next Story**: [US006: Browser Notification Integration](US006-browser-notification-integration.md)  
**⬅️ Previous Story**: [US004: Notification Persistence & History](US004-notification-persistence-history.md)  
**📋 Back to**: [Feature Overview](README.md)