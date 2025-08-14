# US002: Soft Delete System

## 📋 User Story

**As a** coach using the platform  
**I want** to be able to "delete" clients and profiles without losing historical data  
**So that** I can manage my active client list while preserving usage statistics and compliance records

## 💼 Business Value

### Current Problem
- Hard deletion removes clients/coaches and all associated usage data
- Accidental deletions are irreversible, causing data loss and support issues
- GDPR compliance requires data preservation for audit purposes while respecting deletion requests
- Usage statistics become incomplete when clients are deleted

### Business Impact
- **Data Loss Risk**: Irreversible deletion of valuable usage analytics
- **Support Overhead**: Customer support requests to restore accidentally deleted data  
- **Compliance Gap**: Audit trails broken by hard deletions
- **UX Issues**: Users afraid to "delete" due to permanence

### Value Delivered
- **Data Preservation**: Historical usage data always available for analytics
- **User Confidence**: Safe deletion with option to restore
- **Compliance Ready**: Proper audit trails while respecting user intent
- **Business Intelligence**: Complete historical dataset for growth analysis

## 🎯 Acceptance Criteria

### Core Soft Delete Functionality
1. **Client Soft Delete**
   - [ ] Clients can be "deleted" (marked as inactive) without removing data
   - [ ] Soft-deleted clients disappear from normal client lists
   - [ ] Soft-deleted clients can be restored by coaches
   - [ ] Historical usage data remains accessible for analytics

2. **Coach Profile Soft Delete**  
   - [ ] Coach profiles can be deactivated without data loss
   - [ ] Inactive profiles don't appear in coach directories
   - [ ] Profile data preserved for usage analytics and compliance

3. **Query Filtering**
   - [ ] Default queries exclude soft-deleted records
   - [ ] Admin queries can include soft-deleted records when needed
   - [ ] API responses clearly indicate active/inactive status

### User Interface Requirements
4. **Client Management UI**
   - [ ] "Delete" button changes to "Deactivate" with clear explanation
   - [ ] Soft-deleted clients shown in separate "Archived" section
   - [ ] One-click restore functionality for archived clients
   - [ ] Clear visual indicators for client status (active/archived)

5. **Admin Interface**
   - [ ] Admin users can view all clients (active and soft-deleted)
   - [ ] Admin analytics include usage from soft-deleted clients
   - [ ] Permanent delete option for admins (GDPR compliance)

### Data Integrity  
6. **Referential Integrity**
   - [ ] Soft-deleted clients preserve relationships to sessions/usage logs
   - [ ] Foreign key constraints updated to handle soft deletion
   - [ ] Cascade behaviors properly handle soft-deleted references

## 🏗️ Technical Implementation

### Database Schema Changes
```sql
-- Add soft delete fields to existing tables
ALTER TABLE client ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE client ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE client ADD COLUMN deleted_by UUID REFERENCES "user"(id) NULL;

ALTER TABLE coach_profile ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;  
ALTER TABLE coach_profile ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE coach_profile ADD COLUMN deleted_by UUID REFERENCES "user"(id) NULL;

-- Add indexes for performance
CREATE INDEX idx_client_is_active ON client(is_active);
CREATE INDEX idx_client_user_active ON client(user_id, is_active);
CREATE INDEX idx_coach_profile_is_active ON coach_profile(is_active);

-- Create view for active clients (backward compatibility)
CREATE VIEW active_clients AS 
SELECT * FROM client WHERE is_active = TRUE;
```

### Enhanced Models
```python
# packages/core-logic/src/coaching_assistant/models/client.py

class Client(BaseModel):
    """Enhanced Client model with soft delete functionality"""
    
    # Existing fields...
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    
    # Soft delete fields
    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # GDPR fields (existing)
    is_anonymized = Column(Boolean, nullable=False, default=False)
    anonymized_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="clients", foreign_keys=[user_id])
    deleted_by_user = relationship("User", foreign_keys=[deleted_by])
    
    def soft_delete(self, deleted_by_user_id: UUID):
        """Soft delete the client"""
        self.is_active = False
        self.deleted_at = datetime.utcnow()
        self.deleted_by = deleted_by_user_id
    
    def restore(self):
        """Restore soft-deleted client"""
        self.is_active = True
        self.deleted_at = None
        self.deleted_by = None
    
    @property
    def status(self) -> str:
        """Get client status for UI display"""
        if not self.is_active:
            return "archived"
        elif self.is_anonymized:
            return "anonymized"
        else:
            return "active"
    
    def can_be_hard_deleted(self) -> bool:
        """Check if client can be permanently deleted (admin only)"""
        # Can be hard deleted if already anonymized and no recent activity
        recent_activity = datetime.utcnow() - timedelta(days=90)
        return (
            self.is_anonymized and 
            self.is_active == False and
            (self.deleted_at is None or self.deleted_at < recent_activity)
        )

# Query scoping for soft delete
from sqlalchemy.orm import Query
from sqlalchemy.ext.declarative import declared_attr

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    @classmethod  
    def active_only(cls, query: Query) -> Query:
        """Filter query to active records only"""
        return query.filter(cls.is_active == True)
    
    @classmethod
    def include_deleted(cls, query: Query) -> Query:
        """Return query including soft-deleted records"""  
        return query  # No filtering
```

### API Enhancements
```python
# packages/core-logic/src/coaching_assistant/api/clients.py

@router.get("/")
async def list_clients(
    include_archived: bool = Query(False, description="Include soft-deleted clients"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """List clients with optional archived clients"""
    
    query = db.query(Client).filter(Client.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(Client.is_active == True)
    
    clients = query.order_by(Client.created_at.desc()).all()
    
    return {
        "clients": [
            {
                "id": client.id,
                "name": client.name, 
                "email": client.email,
                "status": client.status,
                "session_count": client.session_count,
                "created_at": client.created_at.isoformat(),
                "deleted_at": client.deleted_at.isoformat() if client.deleted_at else None,
                "is_active": client.is_active
            }
            for client in clients
        ],
        "summary": {
            "active_count": len([c for c in clients if c.is_active]),
            "archived_count": len([c for c in clients if not c.is_active]),
            "total_count": len(clients)
        }
    }

@router.delete("/{client_id}")
async def soft_delete_client(
    client_id: UUID,
    permanent: bool = Query(False, description="Permanent deletion (admin only)"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Soft delete a client (or permanent delete if admin)"""
    
    client = db.query(Client).filter(
        and_(Client.id == client_id, Client.user_id == current_user.id)
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Permanent deletion (admin only)
    if permanent:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Permanent deletion requires admin privileges")
        
        if not client.can_be_hard_deleted():
            raise HTTPException(
                status_code=400, 
                detail="Client cannot be permanently deleted. Must be anonymized and archived for 90+ days."
            )
        
        # Check for recent activity
        recent_usage = db.query(UsageLog).filter(
            UsageLog.client_id == client_id,
            UsageLog.created_at > datetime.utcnow() - timedelta(days=90)
        ).first()
        
        if recent_usage:
            raise HTTPException(
                status_code=400,
                detail="Cannot permanently delete client with recent usage activity"
            )
        
        # Permanent deletion
        db.delete(client)
        db.commit()
        return {"message": "Client permanently deleted"}
    
    # Soft deletion (standard operation)
    if not client.is_active:
        raise HTTPException(status_code=400, detail="Client is already archived")
    
    client.soft_delete(current_user.id)
    db.commit()
    
    return {
        "message": f"Client '{client.name}' archived successfully",
        "client": {
            "id": client.id,
            "name": client.name,
            "status": client.status,
            "deleted_at": client.deleted_at.isoformat()
        }
    }

@router.post("/{client_id}/restore")
async def restore_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Restore soft-deleted client"""
    
    client = db.query(Client).filter(
        and_(
            Client.id == client_id, 
            Client.user_id == current_user.id,
            Client.is_active == False  # Only restore archived clients
        )
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Archived client not found")
    
    if client.is_anonymized:
        raise HTTPException(
            status_code=400,
            detail="Cannot restore anonymized client. Anonymization is irreversible."
        )
    
    client.restore()
    db.commit()
    
    return {
        "message": f"Client '{client.name}' restored successfully", 
        "client": {
            "id": client.id,
            "name": client.name,
            "status": client.status
        }
    }
```

### Database Query Patterns
```python
# packages/core-logic/src/coaching_assistant/services/client_service.py

class ClientService:
    """Service layer for client operations with soft delete support"""
    
    @staticmethod
    def get_active_clients(user_id: UUID, db: Session) -> List[Client]:
        """Get all active clients for a user"""
        return db.query(Client).filter(
            and_(Client.user_id == user_id, Client.is_active == True)
        ).order_by(Client.name).all()
    
    @staticmethod  
    def get_all_clients(user_id: UUID, db: Session) -> List[Client]:
        """Get all clients (active and archived) for a user"""
        return db.query(Client).filter(
            Client.user_id == user_id
        ).order_by(Client.is_active.desc(), Client.name).all()
    
    @staticmethod
    def get_client_with_usage(client_id: UUID, user_id: UUID, db: Session) -> dict:
        """Get client details including usage from archived periods"""
        client = db.query(Client).filter(
            and_(Client.id == client_id, Client.user_id == user_id)
        ).first()
        
        if not client:
            return None
            
        # Usage statistics include periods when client was active
        total_usage = db.query(UsageLog).filter(
            UsageLog.client_id == client_id
        ).all()
        
        return {
            "client": client,
            "usage_summary": {
                "total_sessions": len(total_usage),
                "total_minutes": sum(log.duration_minutes for log in total_usage),
                "total_cost": sum(log.cost_usd or 0 for log in total_usage),
                "date_range": {
                    "first_session": min(log.created_at for log in total_usage) if total_usage else None,
                    "last_session": max(log.created_at for log in total_usage) if total_usage else None
                }
            }
        }
```

## 🎨 Frontend Implementation

### Client List Component Updates  
```tsx
// apps/web/app/dashboard/clients/ClientsList.tsx

interface Client {
  id: string;
  name: string;
  email?: string;
  status: 'active' | 'archived' | 'anonymized';
  session_count: number;
  is_active: boolean;
  deleted_at?: string;
}

export function ClientsList() {
  const [showArchived, setShowArchived] = useState(false);
  const [clients, setClients] = useState<Client[]>([]);
  
  const fetchClients = async () => {
    const response = await fetch(`/api/v1/clients?include_archived=${showArchived}`);
    const data = await response.json();
    setClients(data.clients);
  };
  
  const archiveClient = async (clientId: string) => {
    const confirmed = window.confirm(
      'Archive this client? This will hide them from your active client list but preserve all session data. You can restore them later if needed.'
    );
    
    if (confirmed) {
      await fetch(`/api/v1/clients/${clientId}`, { method: 'DELETE' });
      fetchClients(); // Refresh list
    }
  };
  
  const restoreClient = async (clientId: string) => {
    await fetch(`/api/v1/clients/${clientId}/restore`, { method: 'POST' });
    fetchClients(); // Refresh list
  };
  
  const activeClients = clients.filter(c => c.is_active);
  const archivedClients = clients.filter(c => !c.is_active);
  
  return (
    <div className="space-y-6">
      {/* Active Clients Section */}
      <div>
        <h2 className="text-lg font-semibold">Active Clients ({activeClients.length})</h2>
        <ClientTable 
          clients={activeClients}
          onArchive={archiveClient}
          showArchiveButton={true}
        />
      </div>
      
      {/* Archived Clients Section (toggle) */}
      <div>
        <button 
          onClick={() => setShowArchived(!showArchived)}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          {showArchived ? 'Hide' : 'Show'} Archived Clients ({archivedClients.length})
        </button>
        
        {showArchived && archivedClients.length > 0 && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-3">
              Archived clients are hidden from your main list but their session data is preserved.
            </p>
            <ClientTable 
              clients={archivedClients}
              onRestore={restoreClient}
              showRestoreButton={true}
            />
          </div>
        )}
      </div>
    </div>
  );
}

function ClientTable({ 
  clients, 
  onArchive, 
  onRestore, 
  showArchiveButton = false,
  showRestoreButton = false 
}: ClientTableProps) {
  return (
    <table className="min-w-full divide-y divide-gray-200">
      <thead>
        <tr>
          <th>Name</th>
          <th>Sessions</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {clients.map(client => (
          <tr key={client.id} className={!client.is_active ? 'opacity-60' : ''}>
            <td>
              {client.name}
              {!client.is_active && (
                <span className="ml-2 text-xs text-gray-500">(Archived)</span>
              )}
            </td>
            <td>{client.session_count}</td>
            <td>
              <ClientStatusBadge status={client.status} />
            </td>
            <td>
              {showArchiveButton && (
                <button 
                  onClick={() => onArchive(client.id)}
                  className="text-red-600 hover:text-red-900"
                >
                  Archive
                </button>
              )}
              {showRestoreButton && (
                <button 
                  onClick={() => onRestore(client.id)}
                  className="text-blue-600 hover:text-blue-900"
                >
                  Restore
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

## 🧪 Test Scenarios

### Unit Tests
```python
def test_client_soft_delete():
    """Test client soft deletion preserves data"""
    client = create_test_client(db, user_id)
    usage_log = create_usage_log(db, client_id=client.id)
    
    # Soft delete client
    client.soft_delete(user_id)
    db.commit()
    
    # Client should be inactive but data preserved
    assert client.is_active == False
    assert client.deleted_at is not None
    assert client.name == "Test Client"  # Data preserved
    
    # Usage logs should remain accessible
    logs = db.query(UsageLog).filter(UsageLog.client_id == client.id).all()
    assert len(logs) == 1
    
def test_client_restore():
    """Test soft-deleted client can be restored"""
    client = create_test_client(db, user_id)
    client.soft_delete(user_id)
    db.commit()
    
    # Restore client
    client.restore()
    db.commit()
    
    assert client.is_active == True
    assert client.deleted_at is None
    assert client.deleted_by is None
    
def test_active_clients_query_filtering():
    """Test queries properly filter out soft-deleted clients"""
    active_client = create_test_client(db, user_id, name="Active")
    archived_client = create_test_client(db, user_id, name="Archived")
    archived_client.soft_delete(user_id)
    db.commit()
    
    # Standard query should only return active clients
    active_clients = db.query(Client).filter(
        and_(Client.user_id == user_id, Client.is_active == True)
    ).all()
    
    assert len(active_clients) == 1
    assert active_clients[0].name == "Active"
```

### Integration Tests
```bash
# Test: Soft delete and restore workflow
curl -X POST /api/v1/clients \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test Client", "email": "test@example.com"}'

CLIENT_ID=$(echo $response | jq -r '.id')

# Archive the client  
curl -X DELETE /api/v1/clients/$CLIENT_ID \
  -H "Authorization: Bearer $TOKEN"

# Verify client is archived but data preserved
curl -X GET /api/v1/clients?include_archived=true \
  -H "Authorization: Bearer $TOKEN"

# Restore the client
curl -X POST /api/v1/clients/$CLIENT_ID/restore \
  -H "Authorization: Bearer $TOKEN"

# Verify client is active again
curl -X GET /api/v1/clients \
  -H "Authorization: Bearer $TOKEN"
```

## 📊 Success Metrics

### Functional Metrics
- **Data Preservation**: 100% of archived clients retain full historical data
- **Query Performance**: <200ms response time for client lists (including archived)
- **User Experience**: <3 seconds for archive/restore operations
- **Data Integrity**: 0% referential integrity violations after soft deletion

### Business Metrics
- **Support Request Reduction**: 80% reduction in "restore deleted client" support tickets
- **User Confidence**: 95% user satisfaction with "safe deletion" feature
- **Data Analytics**: 100% retention of historical usage data for business intelligence

## ⚡ Performance Considerations

### Database Optimization
- Index on `is_active` column for fast filtering
- Composite index on `(user_id, is_active)` for user-specific queries
- Query optimization to avoid N+1 problems with client relationships

### Scalability Planning
- Soft deletion supports growing client databases (100,000+ clients per user)
- Archive/restore operations scale linearly with client count
- Admin queries with large archived datasets optimized with pagination

## 🔒 Security & Privacy

### Access Control
- Users can only archive/restore their own clients
- Admin users have additional permanent deletion privileges
- Audit logging for all archive/restore operations

### GDPR Compliance
- Soft deletion preserves data for legitimate business interests
- Anonymization still available for full privacy compliance
- Clear distinction between "archive" (reversible) and "anonymize" (permanent)

## 📋 Definition of Done

- [ ] **Database Schema**: Migration adds soft delete fields to Client and CoachProfile
- [ ] **Model Enhancement**: Client and CoachProfile models support soft deletion
- [ ] **API Endpoints**: Archive, restore, and filtered list endpoints working
- [ ] **Query Filtering**: Default queries exclude soft-deleted records
- [ ] **Frontend UI**: Client management interface shows archived clients separately
- [ ] **Admin Interface**: Admin users can view and manage all client states
- [ ] **Unit Tests**: >85% coverage for soft delete functionality
- [ ] **Integration Tests**: End-to-end archive/restore workflow verified
- [ ] **Performance**: Query performance meets <200ms targets
- [ ] **Documentation**: User guide explains archive vs delete vs anonymize
- [ ] **Migration Strategy**: Existing clients properly handled in migration

## 🔄 Dependencies & Risks

### Dependencies
- ✅ Current Client and CoachProfile models are stable
- ⏳ Database migration strategy agreed upon
- ⏳ Frontend client management components identified

### Risks & Mitigations
- **Risk**: Confusion between archive, delete, and anonymize
  - **Mitigation**: Clear UI labeling, help text, confirmation dialogs
- **Risk**: Performance impact of additional filtering
  - **Mitigation**: Proper indexing, query optimization, monitoring
- **Risk**: Complex query patterns for including/excluding archived data
  - **Mitigation**: Service layer abstracts query complexity, comprehensive testing

## 📞 Stakeholders

**Product Owner**: UX/Product Team  
**Technical Lead**: Backend/Frontend Engineering  
**Reviewers**: Legal (Data Retention), Support (User Experience)  
**QA Focus**: Data integrity, User experience, Performance