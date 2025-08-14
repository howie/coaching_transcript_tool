# US006: Browser Notification Integration

## 📊 Story Information
- **Epic**: Event Notification System
- **Priority**: P2 (Medium)
- **Story Points**: 4
- **Sprint**: User Experience Sprint 3
- **Feature Flag**: `enable_browser_notifications`
- **Dependencies**: US002 (Frontend Bell), US005 (Preferences)
- **Assignee**: Frontend Developer

## 👤 User Story
**As a** coaching platform user  
**I want** to receive browser push notifications when important events occur  
**So that** I'm notified even when I'm not actively viewing the dashboard

### Business Value
- **Enhanced Engagement**: Users stay informed even when multitasking
- **Immediate Response**: Critical notifications reach users instantly
- **Modern Experience**: Native browser notifications feel professional
- **Reduced Missed Events**: Users don't miss important transcription completions

## ✅ Acceptance Criteria

### AC1: Browser Permission Request
**Given** I want to enable browser notifications  
**When** I toggle browser notifications in my preferences  
**Then** the system requests browser notification permission

**Permission Requirements:**
- Uses modern Notification API
- Graceful handling if permission denied
- Clear explanation of notification benefits
- Re-request permission if previously denied

### AC2: Native Browser Notifications
**Given** I have browser notifications enabled and permission granted  
**When** a high-priority notification is created (transcription complete/failed)  
**Then** I receive a native browser notification

**Notification Requirements:**
- Shows notification icon, title, and message
- Clicking notification opens relevant session page
- Respects user's browser notification settings
- Works across Chrome, Firefox, Safari, Edge

### AC3: Notification Content & Actions
**Given** I receive a browser notification  
**When** I interact with it  
**Then** I can take relevant actions directly from the notification

**Content Requirements:**
- Title: Clear, concise event description
- Body: Relevant details (session name, status)
- Icon: App logo or notification type icon
- Actions: "View Session", "Mark as Read" (where supported)
- Badge: Unread count on browser tab

### AC4: Smart Notification Logic
**Given** I have the dashboard open and browser notifications enabled  
**When** a notification is created  
**Then** browser notifications are suppressed to avoid duplication

**Smart Logic:**
- Detect if dashboard tab is active/visible
- Suppress browser notifications when tab is focused
- Send browser notifications when tab is background/closed
- Respect quiet hours from user preferences

### AC5: Fallback & Error Handling
**Given** browser notifications fail or aren't supported  
**When** the system tries to send a browser notification  
**Then** it falls back gracefully to in-app notifications only

**Error Handling:**
- Permission denied: Show in-app message, disable setting
- API not supported: Hide browser notification option
- Send failure: Log error, continue with other channels
- Service worker issues: Fallback to basic notifications

## 🧪 TDD Test Implementation

### Frontend Browser Notification Tests (Required: 4 tests)

```typescript
// Test 1: Permission Request (Write First)
describe('BrowserNotificationService', () => {
  beforeEach(() => {
    // Mock Notification API
    global.Notification = {
      permission: 'default',
      requestPermission: jest.fn(),
    } as any;
    
    Object.defineProperty(window, 'Notification', {
      value: global.Notification,
      writable: true,
    });
  });

  it('should request notification permission when enabled', async () => {
    // RED: Permission request logic doesn't exist
    const mockRequestPermission = jest.fn().mockResolvedValue('granted');
    global.Notification.requestPermission = mockRequestPermission;
    
    const service = new BrowserNotificationService();
    const result = await service.requestPermission();
    
    expect(mockRequestPermission).toHaveBeenCalled();
    expect(result).toBe('granted');
  });

  // Test 2: Notification Creation (Write Second)
  it('should create browser notification with proper content', async () => {
    // RED: Notification creation not implemented
    const MockNotificationConstructor = jest.fn();
    global.Notification = MockNotificationConstructor as any;
    Object.assign(global.Notification, { permission: 'granted' });
    
    const service = new BrowserNotificationService();
    const notification = {
      id: '123',
      title: 'Transcription Complete',
      message: 'Your session "Monday Coaching" is ready to view',
      type: 'success',
      metadata: { action_url: '/dashboard/sessions/123' }
    };
    
    await service.showNotification(notification);
    
    expect(MockNotificationConstructor).toHaveBeenCalledWith(
      'Transcription Complete',
      expect.objectContaining({
        body: 'Your session "Monday Coaching" is ready to view',
        icon: expect.stringContaining('/icon'),
        badge: expect.stringContaining('/badge'),
        tag: '123',
        data: expect.objectContaining({
          action_url: '/dashboard/sessions/123'
        })
      })
    );
  });

  // Test 3: Click Handling (Write Third)
  it('should handle notification click to open session', async () => {
    // RED: Click handling not implemented
    const mockNavigate = jest.fn();
    const mockNotification = {
      addEventListener: jest.fn(),
      close: jest.fn(),
      data: { action_url: '/dashboard/sessions/123' }
    };
    
    const MockNotificationConstructor = jest.fn().mockReturnValue(mockNotification);
    global.Notification = MockNotificationConstructor as any;
    Object.assign(global.Notification, { permission: 'granted' });
    
    // Mock router
    jest.mock('next/router', () => ({
      useRouter: () => ({ push: mockNavigate })
    }));
    
    const service = new BrowserNotificationService();
    await service.showNotification({
      id: '123',
      title: 'Test',
      message: 'Test message',
      type: 'success',
      metadata: { action_url: '/dashboard/sessions/123' }
    });
    
    // Simulate click event
    const clickHandler = mockNotification.addEventListener.mock.calls.find(
      call => call[0] === 'click'
    )[1];
    
    clickHandler();
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/sessions/123');
    expect(mockNotification.close).toHaveBeenCalled();
  });

  // Test 4: Tab Visibility Detection (Write Fourth)
  it('should suppress notifications when tab is active', async () => {
    // RED: Visibility detection not implemented
    const MockNotificationConstructor = jest.fn();
    global.Notification = MockNotificationConstructor as any;
    Object.assign(global.Notification, { permission: 'granted' });
    
    // Mock document visibility as visible
    Object.defineProperty(document, 'visibilityState', {
      value: 'visible',
      writable: true,
    });
    
    Object.defineProperty(document, 'hasFocus', {
      value: jest.fn().mockReturnValue(true),
      writable: true,
    });
    
    const service = new BrowserNotificationService();
    const shouldShow = service.shouldShowBrowserNotification();
    
    expect(shouldShow).toBe(false);
    
    // Change to hidden and unfocused
    Object.defineProperty(document, 'visibilityState', {
      value: 'hidden',
      writable: true,
    });
    (document.hasFocus as jest.Mock).mockReturnValue(false);
    
    const shouldShowHidden = service.shouldShowBrowserNotification();
    expect(shouldShowHidden).toBe(true);
  });
});
```

### Integration Tests (Required: 2 tests)

```typescript
// Integration Test 1: Settings Integration (Write First)
describe('Browser Notification Integration', () => {
  it('should integrate with notification settings', async () => {
    // RED: Settings integration not implemented
    const mockUpdatePreferences = jest.fn();
    global.Notification = { permission: 'default', requestPermission: jest.fn().mockResolvedValue('granted') } as any;
    
    render(
      <NotificationSettings 
        preferences={{ browser_notifications: false }}
        onUpdate={mockUpdatePreferences}
      />
    );
    
    const browserToggle = screen.getByLabelText('Browser notifications');
    await userEvent.click(browserToggle);
    
    // Should request permission first
    expect(global.Notification.requestPermission).toHaveBeenCalled();
    
    // Then update preferences
    await waitFor(() => {
      expect(mockUpdatePreferences).toHaveBeenCalledWith({
        browser_notifications: true
      });
    });
  });

  // Integration Test 2: SSE Integration (Write Second)
  it('should show browser notifications for SSE events when tab hidden', async () => {
    // RED: SSE integration not implemented
    const MockNotificationConstructor = jest.fn();
    global.Notification = MockNotificationConstructor as any;
    Object.assign(global.Notification, { permission: 'granted' });
    
    // Mock tab as hidden
    Object.defineProperty(document, 'visibilityState', {
      value: 'hidden',
      writable: true,
    });
    
    const mockAddNotification = jest.fn();
    const { result } = renderHook(() => useNotificationSSE({
      onNotification: mockAddNotification
    }));
    
    // Simulate SSE notification
    const sseEvent = new MessageEvent('notification', {
      data: JSON.stringify({
        id: '123',
        title: 'Transcription Complete',
        message: 'Your transcription is ready',
        type: 'success'
      })
    });
    
    // Should show browser notification since tab is hidden
    await act(async () => {
      window.dispatchEvent(sseEvent);
    });
    
    expect(MockNotificationConstructor).toHaveBeenCalledWith(
      'Transcription Complete',
      expect.objectContaining({
        body: 'Your transcription is ready'
      })
    );
  });
});
```

## 🛠️ Technical Implementation

### Browser Notification Service

```typescript
// services/browserNotificationService.ts
export class BrowserNotificationService {
  private static instance: BrowserNotificationService;
  
  static getInstance(): BrowserNotificationService {
    if (!BrowserNotificationService.instance) {
      BrowserNotificationService.instance = new BrowserNotificationService();
    }
    return BrowserNotificationService.instance;
  }
  
  async requestPermission(): Promise<NotificationPermission> {
    if (!this.isSupported()) {
      throw new Error('Browser notifications not supported');
    }
    
    if (Notification.permission === 'granted') {
      return 'granted';
    }
    
    if (Notification.permission === 'denied') {
      return 'denied';
    }
    
    try {
      const permission = await Notification.requestPermission();
      return permission;
    } catch (error) {
      console.error('Failed to request notification permission:', error);
      return 'denied';
    }
  }
  
  async showNotification(notification: NotificationData): Promise<void> {
    if (!this.canShow()) {
      return;
    }
    
    if (!this.shouldShowBrowserNotification()) {
      // Tab is active, skip browser notification
      return;
    }
    
    try {
      const browserNotification = new Notification(notification.title, {
        body: notification.message,
        icon: this.getNotificationIcon(notification.type),
        badge: '/images/notification-badge.png',
        tag: notification.id, // Prevents duplicate notifications
        data: {
          notificationId: notification.id,
          action_url: notification.metadata?.action_url,
          type: notification.type
        },
        actions: this.getNotificationActions(notification),
        requireInteraction: notification.type === 'error', // Keep error notifications until clicked
        silent: false
      });
      
      // Handle click events
      browserNotification.addEventListener('click', () => {
        this.handleNotificationClick(browserNotification);
      });
      
      // Handle action button clicks
      browserNotification.addEventListener('notificationclick', (event) => {
        this.handleNotificationAction(event);
      });
      
      // Auto-close success notifications after 5 seconds
      if (notification.type === 'success') {
        setTimeout(() => {
          browserNotification.close();
        }, 5000);
      }
      
    } catch (error) {
      console.error('Failed to show browser notification:', error);
      // Fallback to toast notification
      this.showFallbackNotification(notification);
    }
  }
  
  shouldShowBrowserNotification(): boolean {
    // Don't show if tab is active and focused
    return document.visibilityState === 'hidden' || !document.hasFocus();
  }
  
  private isSupported(): boolean {
    return 'Notification' in window && 'serviceWorker' in navigator;
  }
  
  private canShow(): boolean {
    return this.isSupported() && Notification.permission === 'granted';
  }
  
  private getNotificationIcon(type: string): string {
    const iconMap = {
      success: '/images/icons/success-notification.png',
      error: '/images/icons/error-notification.png',
      info: '/images/icons/info-notification.png',
      warning: '/images/icons/warning-notification.png'
    };
    
    return iconMap[type] || '/images/icons/default-notification.png';
  }
  
  private getNotificationActions(notification: NotificationData): NotificationAction[] {
    const actions: NotificationAction[] = [
      {
        action: 'view',
        title: 'View Details',
        icon: '/images/icons/view-action.png'
      }
    ];
    
    if (notification.type === 'success') {
      actions.push({
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/images/icons/dismiss-action.png'
      });
    }
    
    return actions;
  }
  
  private handleNotificationClick(notification: Notification): void {
    const data = notification.data;
    
    // Focus or open the window
    if (window.focus) {
      window.focus();
    }
    
    // Navigate to relevant page
    if (data?.action_url) {
      const router = useRouter();
      router.push(data.action_url);
    }
    
    // Mark notification as read
    if (data?.notificationId) {
      this.markNotificationAsRead(data.notificationId);
    }
    
    notification.close();
  }
  
  private handleNotificationAction(event: NotificationEvent): void {
    const action = event.action;
    const data = event.notification.data;
    
    switch (action) {
      case 'view':
        this.handleNotificationClick(event.notification);
        break;
      case 'dismiss':
        if (data?.notificationId) {
          this.markNotificationAsRead(data.notificationId);
        }
        event.notification.close();
        break;
    }
  }
  
  private async markNotificationAsRead(notificationId: string): Promise<void> {
    try {
      await apiClient.markNotificationAsRead(notificationId);
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }
  
  private showFallbackNotification(notification: NotificationData): void {
    // Show toast notification as fallback
    toast(notification.title, {
      description: notification.message,
      type: notification.type === 'success' ? 'success' : 'error'
    });
  }
}

// Export singleton instance
export const browserNotificationService = BrowserNotificationService.getInstance();
```

### Enhanced Notification Context Integration

```typescript
// contexts/notification-context.tsx - Enhanced with browser notifications
export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  
  // Load user preferences
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const prefs = await apiClient.getNotificationPreferences();
        setPreferences(prefs);
        
        // Initialize browser notifications if enabled
        if (prefs.browser_notifications) {
          await browserNotificationService.requestPermission();
        }
      } catch (error) {
        console.error('Failed to load notification preferences:', error);
      }
    };
    
    loadPreferences();
  }, []);
  
  const handleSSENotification = useCallback(async (notification: Notification) => {
    // Add to in-app notifications
    addNotification(notification);
    
    // Show browser notification if enabled and appropriate
    if (preferences?.browser_notifications) {
      try {
        await browserNotificationService.showNotification(notification);
      } catch (error) {
        console.error('Failed to show browser notification:', error);
      }
    }
    
    // Update unread count
    if (notification.status === 'unread') {
      setUnreadCount(prev => prev + 1);
    }
  }, [addNotification, preferences]);
  
  // ... rest of context implementation
};
```

### Settings Component Integration

```typescript
// components/notifications/NotificationSettings.tsx - Enhanced with browser notifications
export const NotificationSettings: React.FC<NotificationSettingsProps> = ({
  preferences,
  onUpdate
}) => {
  const [browserSupported, setBrowserSupported] = useState(false);
  const [browserPermission, setBrowserPermission] = useState<NotificationPermission>('default');
  
  useEffect(() => {
    setBrowserSupported(browserNotificationService.isSupported());
    if (browserNotificationService.isSupported()) {
      setBrowserPermission(Notification.permission);
    }
  }, []);
  
  const handleBrowserNotificationToggle = async (enabled: boolean) => {
    if (enabled) {
      try {
        const permission = await browserNotificationService.requestPermission();
        setBrowserPermission(permission);
        
        if (permission === 'granted') {
          await onUpdate?.({ ...preferences, browser_notifications: true });
        } else {
          // Permission denied, show explanation
          toast.error('Browser notifications require permission. Please check your browser settings.');
          return;
        }
      } catch (error) {
        console.error('Failed to enable browser notifications:', error);
        toast.error('Failed to enable browser notifications. Please try again.');
        return;
      }
    } else {
      await onUpdate?.({ ...preferences, browser_notifications: false });
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Other settings... */}
      
      <div>
        <h3 className="text-lg font-medium mb-4">Delivery Channels</h3>
        <div className="space-y-3">
          {/* Other channel settings... */}
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium">Browser notifications</label>
              {!browserSupported && (
                <p className="text-xs text-gray-500 mt-1">
                  Not supported in this browser
                </p>
              )}
              {browserSupported && browserPermission === 'denied' && (
                <p className="text-xs text-amber-600 mt-1">
                  Permission denied. Please enable in browser settings.
                </p>
              )}
            </div>
            <Switch
              checked={preferences?.browser_notifications && browserPermission === 'granted'}
              onChange={handleBrowserNotificationToggle}
              disabled={!browserSupported || browserPermission === 'denied'}
            />
          </div>
        </div>
      </div>
      
      {/* Other settings sections... */}
    </div>
  );
};
```

### Service Worker Registration (Optional Enhancement)

```typescript
// public/sw.js - Service worker for enhanced browser notifications
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const data = event.notification.data;
  const action = event.action;
  
  if (action === 'view' || !action) {
    // Open the app to the relevant page
    event.waitUntil(
      clients.openWindow(data.action_url || '/dashboard')
    );
  } else if (action === 'dismiss') {
    // Mark as read via API
    event.waitUntil(
      fetch(`/api/notifications/${data.notificationId}/read`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${data.token}`,
          'Content-Type': 'application/json'
        }
      })
    );
  }
});

self.addEventListener('notificationclose', (event) => {
  // Optional: Track notification dismissal analytics
  console.log('Notification closed:', event.notification.data);
});
```

## 📊 Definition of Done Checklist

### Testing Requirements
- [ ] **Frontend notification tests**: 4/4 tests using TDD methodology
- [ ] **Integration tests**: 2/2 tests covering settings and SSE integration
- [ ] **Browser compatibility**: Tested in Chrome, Firefox, Safari, Edge
- [ ] **Permission scenarios**: Granted, denied, and unsupported cases tested
- [ ] **Fallback behavior**: Graceful degradation when notifications fail

### Code Quality Requirements
- [ ] **Permission handling**: Proper request and error handling
- [ ] **Memory management**: Event listeners properly cleaned up
- [ ] **Error recovery**: Fallback to in-app notifications
- [ ] **Performance**: No impact on main thread performance
- [ ] **Security**: No sensitive data in notification content

### User Experience Requirements
- [ ] **Clear permissions**: Users understand why permissions are needed
- [ ] **Smart suppression**: No duplicate notifications when tab is active
- [ ] **Actionable content**: Notifications provide clear next steps
- [ ] **Respectful timing**: Honors quiet hours and frequency settings
- [ ] **Accessibility**: Works with screen readers and assistive technology

### Browser Compatibility Requirements
- [ ] **Modern browsers**: Chrome 50+, Firefox 44+, Safari 10+, Edge 14+
- [ ] **Graceful degradation**: Hidden when not supported
- [ ] **Permission states**: Handles all permission scenarios
- [ ] **Mobile support**: Works on mobile browsers where supported
- [ ] **Service worker**: Enhanced functionality with SW registration

### Integration Requirements
- [ ] **Preferences sync**: Browser notification setting saved to backend
- [ ] **SSE integration**: Real-time notifications trigger browser notifications
- [ ] **Quiet hours**: Browser notifications respect user quiet hours
- [ ] **Navigation**: Clicking notifications navigates to correct pages
- [ ] **Badge updates**: Browser tab badge shows unread count

## 🚀 Implementation Notes

### Browser Support Strategy
- **Progressive enhancement**: Feature available where supported
- **Feature detection**: Check for Notification API and ServiceWorker
- **Graceful fallback**: In-app notifications when browser notifications unavailable
- **Clear messaging**: Inform users when features aren't available

### Permission Best Practices
- **Contextual requests**: Ask for permission when user enables feature
- **Clear value proposition**: Explain benefits before requesting permission
- **Handle denial gracefully**: Don't repeatedly ask if denied
- **Settings integration**: Allow users to manage permissions from settings

### Performance Considerations
- **Lazy loading**: Only load notification service when needed
- **Memory cleanup**: Remove event listeners on component unmount
- **Throttling**: Prevent notification spam with intelligent batching
- **Background efficiency**: Minimal CPU usage when tab is hidden

### Security & Privacy
- **No sensitive data**: Only show safe information in notifications
- **User control**: Users can disable at any time
- **Respect preferences**: Honor all user notification preferences
- **Audit trail**: Log notification delivery for troubleshooting

---

**⬅️ Previous Story**: [US005: Notification Preferences & Settings](US005-notification-preferences-settings.md)  
**📋 Back to**: [Feature Overview](README.md)  
**🎯 Epic Complete**: All 6 user stories documented