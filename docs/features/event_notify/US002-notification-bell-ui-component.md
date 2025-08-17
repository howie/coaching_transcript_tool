# US002: Notification Bell UI Component

## 📊 Story Information
- **Epic**: Event Notification System
- **Priority**: P0 (Critical)
- **Story Points**: 5
- **Sprint**: Foundation Sprint 1
- **Feature Flag**: `enable_notifications`
- **Dependencies**: US001 (Backend API), Dashboard Header Component
- **Assignee**: Frontend Developer

## 👤 User Story
**As a** coaching platform user  
**I want** to see a notification bell icon in the dashboard header  
**So that** I can easily access my notifications and see unread counts at a glance

### Business Value
- **User Experience**: Provides immediate visual feedback for important updates
- **Engagement**: Keeps users informed without interrupting their workflow  
- **Professional Feel**: Modern UX pattern expected by users
- **Discoverability**: Makes notification system visible and accessible

## ✅ Acceptance Criteria

### AC1: Notification Bell Icon Display
**Given** I am logged into the dashboard  
**When** I view the header  
**Then** I see a bell icon in the top-right area next to the user menu

**UI Requirements:**
- Bell icon uses Heroicons outline bell icon
- Icon has hover state with color change
- Icon is accessible with proper ARIA labels
- Icon size matches other header icons (20x20px)

### AC2: Unread Count Badge
**Given** I have unread notifications  
**When** I view the notification bell  
**Then** I see a red badge with the unread count

**Given** I have no unread notifications  
**When** I view the notification bell  
**Then** I see no badge on the bell icon

**Badge Requirements:**
- Red circular badge positioned top-right of bell icon
- Shows count up to 99, then displays "99+"
- Badge disappears when count reaches 0
- Smooth animation when count changes

### AC3: Notification Dropdown Panel
**Given** I click the notification bell  
**When** the dropdown opens  
**Then** I see a panel with my recent notifications

**Dropdown Requirements:**
- Panel width: 320px, max height: 400px with scroll
- Shows most recent 10 notifications
- Each notification shows: title, time ago, read/unread status
- Empty state when no notifications exist
- "View All" link at bottom when more than 10 notifications

### AC4: Notification Interaction
**Given** I click on a notification in the dropdown  
**When** the notification has a related session  
**Then** I navigate to that session's detail page and notification is marked as read

**Given** I click "Mark all as read" in the dropdown  
**When** the action completes  
**Then** all notifications are marked as read and badge count becomes 0

### AC5: Real-time Updates (Basic)
**Given** a new notification is created for me  
**When** I have the dashboard open  
**Then** the bell badge count updates within 30 seconds

**Note**: Full real-time SSE implementation is handled in US003

## 🧪 TDD Test Implementation

### MANDATORY: Follow Red-Green-Refactor Cycle
All code for this story MUST be written using strict TDD methodology:

1. **RED**: Write failing test first
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Improve structure while tests pass
4. **COMMIT**: Separate structural from behavioral changes

### Frontend Component Tests (Required: 7 tests)

#### Test Sequence (MUST FOLLOW THIS ORDER)

```typescript
// Test 1: Basic Rendering (Write First)
describe('NotificationBell', () => {
  it('should render bell icon with proper accessibility', () => {
    // RED: Component doesn't exist yet
    render(<NotificationBell />);
    
    const bellIcon = screen.getByRole('button', { name: /notifications/i });
    expect(bellIcon).toBeInTheDocument();
    expect(bellIcon).toHaveAttribute('aria-label', 'Open notifications');
  });

  // Test 2: Badge Display Logic (Write Second, after Test 1 passes)
  it('should display unread count badge when notifications exist', () => {
    // RED: Badge logic not implemented
    const mockNotifications = [
      { id: '1', status: 'unread', title: 'Test 1' },
      { id: '2', status: 'unread', title: 'Test 2' }
    ];
    
    render(<NotificationBell notifications={mockNotifications} />);
    
    const badge = screen.getByText('2');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-red-500');
  });

  // Test 3: No Badge When Empty (Write Third)
  it('should not display badge when no unread notifications', () => {
    // RED: Badge hiding logic not implemented
    const mockNotifications = [
      { id: '1', status: 'read', title: 'Test 1' }
    ];
    
    render(<NotificationBell notifications={mockNotifications} />);
    
    expect(screen.queryByText('1')).not.toBeInTheDocument();
  });

  // Test 4: Dropdown Toggle (Write Fourth)
  it('should open dropdown panel when bell icon clicked', async () => {
    // RED: Dropdown functionality not implemented
    const user = userEvent.setup();
    render(<NotificationBell />);
    
    const bellButton = screen.getByRole('button', { name: /notifications/i });
    await user.click(bellButton);
    
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  // Test 5: Notification List Display (Write Fifth)
  it('should display notification list in dropdown', async () => {
    // RED: Notification list rendering not implemented
    const mockNotifications = [
      {
        id: '1',
        title: 'Transcription Complete',
        message: 'Your audio is ready',
        created_at: '2025-01-01T10:00:00Z',
        status: 'unread'
      },
      {
        id: '2', 
        title: 'Processing Started',
        message: 'Your transcription is being processed',
        created_at: '2025-01-01T09:30:00Z', 
        status: 'read'
      }
    ];
    
    const user = userEvent.setup();
    render(<NotificationBell notifications={mockNotifications} />);
    
    await user.click(screen.getByRole('button', { name: /notifications/i }));
    
    expect(screen.getByText('Transcription Complete')).toBeInTheDocument();
    expect(screen.getByText('Processing Started')).toBeInTheDocument();
    expect(screen.getByText('2 hours ago')).toBeInTheDocument(); // Relative time
  });

  // Test 6: Notification Click Navigation (Write Sixth)
  it('should navigate to session when notification clicked', async () => {
    // RED: Navigation logic not implemented
    const mockNavigate = jest.fn();
    jest.mock('next/navigation', () => ({
      useRouter: () => ({ push: mockNavigate })
    }));
    
    const mockNotifications = [
      {
        id: '1',
        title: 'Transcription Complete', 
        metadata: { action_url: '/dashboard/sessions/123' },
        related_session_id: '123'
      }
    ];
    
    const user = userEvent.setup();
    render(<NotificationBell notifications={mockNotifications} />);
    
    await user.click(screen.getByRole('button', { name: /notifications/i }));
    await user.click(screen.getByText('Transcription Complete'));
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard/sessions/123');
  });

  // Test 7: Mark All as Read (Write Seventh)
  it('should mark all notifications as read when button clicked', async () => {
    // RED: Mark as read functionality not implemented  
    const mockMarkAllAsRead = jest.fn();
    const mockNotifications = [
      { id: '1', status: 'unread', title: 'Test 1' },
      { id: '2', status: 'unread', title: 'Test 2' }
    ];
    
    const user = userEvent.setup();
    render(
      <NotificationBell 
        notifications={mockNotifications}
        onMarkAllAsRead={mockMarkAllAsRead}
      />
    );
    
    await user.click(screen.getByRole('button', { name: /notifications/i }));
    await user.click(screen.getByText('Mark all as read'));
    
    expect(mockMarkAllAsRead).toHaveBeenCalled();
  });
});
```

### API Integration Tests (Required: 3 tests)

```typescript
// Integration Test 1: Fetch on Mount (Write First)
describe('NotificationBell API Integration', () => {
  it('should fetch notifications when component mounts', async () => {
    // RED: API integration not implemented
    const mockApiClient = {
      getNotifications: jest.fn().mockResolvedValue({
        notifications: [],
        total: 0
      }),
      getUnreadCount: jest.fn().mockResolvedValue({ unread_count: 0 })
    };
    
    render(<NotificationBell apiClient={mockApiClient} />);
    
    await waitFor(() => {
      expect(mockApiClient.getNotifications).toHaveBeenCalledWith({
        page: 1,
        limit: 10,
        status: 'all'
      });
      expect(mockApiClient.getUnreadCount).toHaveBeenCalled();
    });
  });

  // Integration Test 2: Error Handling (Write Second)
  it('should handle API errors gracefully', async () => {
    // RED: Error handling not implemented
    const mockApiClient = {
      getNotifications: jest.fn().mockRejectedValue(new Error('API Error')),
      getUnreadCount: jest.fn().mockRejectedValue(new Error('API Error'))
    };
    
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    
    render(<NotificationBell apiClient={mockApiClient} />);
    
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Failed to load notifications:', expect.any(Error));
    });
    
    // Should show error state in UI
    expect(screen.getByText('Failed to load notifications')).toBeInTheDocument();
    
    consoleSpy.mockRestore();
  });

  // Integration Test 3: Polling Updates (Write Third)  
  it('should poll for notification updates every 30 seconds', async () => {
    // RED: Polling logic not implemented
    jest.useFakeTimers();
    
    const mockApiClient = {
      getNotifications: jest.fn().mockResolvedValue({ notifications: [], total: 0 }),
      getUnreadCount: jest.fn().mockResolvedValue({ unread_count: 0 })
    };
    
    render(<NotificationBell apiClient={mockApiClient} />);
    
    // Initial call
    await waitFor(() => {
      expect(mockApiClient.getUnreadCount).toHaveBeenCalledTimes(1);
    });
    
    // Fast-forward 30 seconds
    jest.advanceTimersByTime(30000);
    
    await waitFor(() => {
      expect(mockApiClient.getUnreadCount).toHaveBeenCalledTimes(2);
    });
    
    jest.useRealTimers();
  });
});
```

## 🛠️ Technical Implementation

### Component Architecture
```typescript
// NotificationBell.tsx - Main component
interface NotificationBellProps {
  className?: string;
  maxDisplayCount?: number;
  pollingInterval?: number;
}

// NotificationDropdown.tsx - Dropdown panel  
interface NotificationDropdownProps {
  notifications: Notification[];
  isOpen: boolean;
  onClose: () => void;
  onNotificationClick: (notification: Notification) => void;
  onMarkAllAsRead: () => void;
}

// NotificationItem.tsx - Individual notification
interface NotificationItemProps {
  notification: Notification;
  onClick: (notification: Notification) => void;
}

// Types
interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  status: 'unread' | 'read' | 'archived';
  metadata: Record<string, any>;
  related_session_id?: string;
  created_at: string;
  read_at?: string;
}
```

### Component Integration with Dashboard Header
```typescript
// apps/web/components/layout/dashboard-header.tsx
import { NotificationBell } from '@/components/notifications/NotificationBell';

export function DashboardHeader() {
  // ... existing code ...
  
  return (
    <header className="bg-dashboard-header shadow-dark border-b border-dashboard-accent border-opacity-20 sticky top-0 z-50">
      <div className="flex justify-between items-center h-16 px-4">
        {/* Left side - existing code */}
        
        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Replace existing bell button with NotificationBell component */}
          <NotificationBell />
          
          {/* Help dropdown - existing code */}
          {/* User dropdown - existing code */}
        </div>
      </div>
    </header>
  );
}
```

### Styling & Design System
```css
/* Notification Bell Styles */
.notification-bell {
  @apply relative p-2 text-white hover:text-dashboard-accent transition-colors rounded-md hover:bg-dashboard-accent hover:bg-opacity-10;
}

.notification-badge {
  @apply absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full min-w-5 h-5 flex items-center justify-center font-medium;
  @apply transform transition-transform duration-200 ease-out;
}

.notification-dropdown {
  @apply absolute right-0 mt-2 w-80 max-h-96 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-50;
}

.notification-item {
  @apply px-4 py-3 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors;
}

.notification-item.unread {
  @apply bg-blue-50 dark:bg-blue-900/20;
}

.notification-item.unread::before {
  content: '';
  @apply absolute left-2 top-1/2 w-2 h-2 bg-blue-500 rounded-full transform -translate-y-1/2;
}
```

### API Client Integration
```typescript
// lib/api.ts - Extend existing API client
class ApiClient {
  // ... existing methods ...

  async getNotifications(params?: {
    page?: number;
    limit?: number;
    status?: 'unread' | 'read' | 'all';
    type?: string;
  }): Promise<NotificationListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());  
    if (params?.status) searchParams.set('status', params.status);
    if (params?.type) searchParams.set('type', params.type);
    
    const response = await this.fetcher(`${this.baseUrl}/api/notifications?${searchParams}`, {
      headers: await this.getHeaders(),
    });
    
    await this.handleResponse(response);
    return response.json();
  }

  async getUnreadCount(): Promise<{ unread_count: number; last_notification_at?: string }> {
    const response = await this.fetcher(`${this.baseUrl}/api/notifications/unread-count`, {
      headers: await this.getHeaders(),
    });
    
    await this.handleResponse(response);
    return response.json();
  }

  async markNotificationAsRead(id: string): Promise<void> {
    const response = await this.fetcher(`${this.baseUrl}/api/notifications/${id}/read`, {
      method: 'PATCH',
      headers: await this.getHeaders(),
    });
    
    await this.handleResponse(response);
  }

  async markAllNotificationsAsRead(): Promise<void> {
    const response = await this.fetcher(`${this.baseUrl}/api/notifications/read-all`, {
      method: 'PATCH', 
      headers: await this.getHeaders(),
    });
    
    await this.handleResponse(response);
  }
}
```

### State Management with React Context
```typescript
// contexts/notification-context.tsx
interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
  refreshNotifications: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Polling logic
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const { unread_count } = await apiClient.getUnreadCount();
        setUnreadCount(unread_count);
      } catch (err) {
        console.error('Failed to poll unread count:', err);
      }
    }, 30000); // 30 seconds
    
    return () => clearInterval(pollInterval);
  }, []);
  
  // ... implementation
};
```

## 📊 Definition of Done Checklist

### Testing Requirements
- [ ] **Unit tests written first (TDD)**: 7/7 component tests using Red-Green-Refactor
- [ ] **API integration tests**: 3/3 tests covering API interactions  
- [ ] **Test coverage >80%**: Frontend component coverage measured and meets threshold
- [ ] **All tests passing**: No failing tests in CI/CD pipeline
- [ ] **E2E test**: Full user workflow tested in browser

### Code Quality Requirements
- [ ] **TDD cycle followed**: Every component feature preceded by failing test
- [ ] **Tidy First approach**: Component refactoring separated from feature additions
- [ ] **Code review completed**: At least one frontend team member approval
- [ ] **No linter warnings**: ESLint, TypeScript all passing
- [ ] **Type safety**: All props and state properly typed

### Accessibility Requirements
- [ ] **ARIA labels**: Proper labels for screen readers
- [ ] **Keyboard navigation**: Bell and dropdown accessible via keyboard
- [ ] **Focus management**: Proper focus handling when dropdown opens/closes
- [ ] **Color contrast**: Badge and text meet WCAG AA standards
- [ ] **Screen reader testing**: Tested with actual screen reader software

### Performance Requirements
- [ ] **Bundle size**: Component adds <5KB to main bundle
- [ ] **Render performance**: No unnecessary re-renders or prop drilling
- [ ] **Memory leaks**: No intervals or event listeners left running
- [ ] **API optimization**: Efficient polling with request deduplication

### UI/UX Requirements
- [ ] **Design system compliance**: Uses existing color tokens and spacing
- [ ] **Responsive design**: Works properly on mobile and desktop  
- [ ] **Loading states**: Proper feedback during API requests
- [ ] **Error states**: Graceful handling of API failures
- [ ] **Empty states**: Clear messaging when no notifications exist

## 🚀 Implementation Notes

### Progressive Enhancement Strategy
1. **Basic Static Bell**: Start with non-functional bell icon
2. **Badge Logic**: Add unread count display  
3. **Dropdown Panel**: Implement notification list display
4. **API Integration**: Connect to backend notification endpoints
5. **Polling Updates**: Add automatic refresh mechanism
6. **Polish & Animations**: Smooth transitions and micro-interactions

### Error Handling Strategy
```typescript
// Graceful degradation for API failures
const NotificationBell = () => {
  const [error, setError] = useState<string | null>(null);
  
  const handleApiError = (err: Error) => {
    console.error('Notification API error:', err);
    setError('Unable to load notifications');
    
    // Show toast notification to user
    toast.error('Failed to load notifications. Please refresh the page.');
  };
  
  // Retry logic with exponential backoff
  const retryFetch = async (attempt = 1) => {
    try {
      await fetchNotifications();
    } catch (err) {
      if (attempt < 3) {
        setTimeout(() => retryFetch(attempt + 1), Math.pow(2, attempt) * 1000);
      } else {
        handleApiError(err as Error);
      }
    }
  };
};
```

### Performance Optimizations
- **Memoization**: Use `React.memo` for notification items to prevent unnecessary re-renders
- **Virtual scrolling**: If notification list grows large (>50 items)
- **Request deduplication**: Prevent multiple simultaneous API calls
- **Efficient polling**: Only poll when tab is active using `document.visibilityState`

### Accessibility Considerations
- **Screen reader support**: Announce new notifications using `aria-live` regions
- **Keyboard navigation**: Allow keyboard users to open dropdown and navigate notifications  
- **High contrast mode**: Ensure badge is visible in Windows high contrast mode
- **Reduced motion**: Respect `prefers-reduced-motion` for badge animations

---

**🔄 Next Story**: [US003: SSE Real-time Updates](US003-sse-real-time-updates.md)  
**⬅️ Previous Story**: [US001: Real-time Notification Foundation](US001-real-time-notification-foundation.md)  
**📋 Back to**: [Feature Overview](README.md)