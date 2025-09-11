'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PlusIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Modal } from '@/components/ui/modal';
import { useI18n } from '@/contexts/i18n-context';
import { useAuth } from '@/contexts/auth-context';
import { apiClient } from '@/lib/api';
import { ClientModal } from '@/components/ClientModal';

interface Client {
  id: string;
  name: string;
  is_anonymized: boolean;
}

interface CoachingSession {
  id: string;
  session_date: string;
  client: Client;
  duration_min: number;
  fee_currency: string;
  fee_amount: number;
  fee_display: string;
  duration_display: string;
  transcription_session_id?: string;
  transcription_session?: {
    id: string;
    status: 'uploading' | 'pending' | 'processing' | 'completed' | 'failed';
    title: string;
    segments_count: number;
  };
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface SessionFormData {
  session_date: string;
  client_id: string;
  duration_min: string;
  fee_currency: string;
  fee_amount: string;
  notes: string;
}


const SessionsPage = () => {
  const { t } = useI18n();
  const { logout } = useAuth();
  const router = useRouter();
  const [sessions, setSessions] = useState<CoachingSession[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [currencies, setCurrencies] = useState<{value: string, label: string}[]>([
    { value: 'TWD', label: `TWD - ${t('sessions.currency.twd')}` },
    { value: 'USD', label: `USD - ${t('sessions.currency.usd')}` },
    { value: 'EUR', label: `EUR - ${t('sessions.currency.eur')}` },
    { value: 'JPY', label: `JPY - ${t('sessions.currency.jpy')}` },
    { value: 'CNY', label: `CNY - ${t('sessions.currency.cny')}` },
    { value: 'HKD', label: `HKD - ${t('sessions.currency.hkd')}` },
    { value: 'GBP', label: `GBP - ${t('sessions.currency.gbp')}` },
    { value: 'AUD', label: `AUD - ${t('sessions.currency.aud')}` },
    { value: 'CAD', label: `CAD - ${t('sessions.currency.cad')}` },
    { value: 'SGD', label: `SGD - ${t('sessions.currency.sgd')}` }
  ]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showClientModal, setShowClientModal] = useState(false);
  const [formData, setFormData] = useState<SessionFormData>({
    session_date: new Date().toISOString().split('T')[0],
    client_id: '',
    duration_min: '60',
    fee_currency: 'TWD',
    fee_amount: '0',
    notes: ''
  });
  const [loadingLastSession, setLoadingLastSession] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    from_date: '',
    to_date: '',
    client_id: '',
    currency: ''
  });
  const pageSize = 20;

  const getTranscriptionStatusBadge = (session: CoachingSession) => {
    if (!session.transcription_session_id && !session.transcription_session) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
          {t('sessions.noTranscript')}
        </span>
      );
    }

    const status = session.transcription_session?.status || 'unknown';
    
    switch (status) {
      case 'uploading':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
            {t('sessions.uploading')}
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">
            {t('sessions.pending')}
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300">
            {t('sessions.processing')}
          </span>
        );
      case 'completed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
            {t('sessions.completed')}
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300">
            {t('sessions.failed')}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
            {t('sessions.unknownStatus')}
          </span>
        );
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchSessions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, filters]);

  // Load last session data when client is selected (only when modal is open)
  useEffect(() => {
    console.log('🔄 useEffect triggered:', { 
      showModal, 
      client_id: formData.client_id
    });
    
    if (showModal && formData.client_id) {
      console.log('✅ Conditions met, fetching last session data for:', formData.client_id);
      fetchLastSessionData(formData.client_id);
    } else {
      console.log('❌ Conditions not met:', {
        showModal,
        hasClientId: !!formData.client_id
      });
    }
  }, [formData.client_id, showModal]);

  const fetchInitialData = async () => {
    try {
      const clientsData = await apiClient.getClients(1, 1000);
      setClients(clientsData.items || []);
      
      // Try to fetch currencies from API, fallback to defaults if fails
      try {
        const currenciesData = await apiClient.getCurrencies();
        // Validate that data is an array with the expected structure
        if (Array.isArray(currenciesData) && currenciesData.length > 0 && 
            currenciesData.every(item => item && typeof item === 'object' && 'value' in item && 'label' in item)) {
          setCurrencies(currenciesData);
        } else {
          console.warn('Invalid currency data format, using defaults');
        }
      } catch (error) {
        console.log('Using default currencies');
      }
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
      // Set empty array as fallback
      setClients([]);
    }
  };

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSessions(currentPage, pageSize, {
        ...filters,
        sort: '-session_date'
      });
      setSessions(data.items);
      setTotalPages(data.total_pages);
    } catch (error: any) {
      console.error('Failed to fetch sessions:', error);
      
      // Check for authorization errors
      const status = error.status;
      if (status === 401 || status === 403) {
        console.log(`Sessions fetch error (${status}): Unauthorized access, logging out...`);
        logout();
        router.push('/login');
        return;
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        session_date: formData.session_date,
        client_id: formData.client_id,
        source: "CLIENT",  // Default to CLIENT source
        duration_min: parseInt(formData.duration_min),
        fee_currency: formData.fee_currency,
        fee_amount: formData.fee_amount ? parseInt(formData.fee_amount) : 0,
        notes: formData.notes
      };

      await apiClient.createSession(payload);

      setShowModal(false);
      resetForm();
      fetchSessions();
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  };

  const handleDelete = async (session: CoachingSession) => {
    if (!confirm(t('sessions.confirmDelete'))) return;

    try {
      await apiClient.deleteSession(session.id);
      fetchSessions();
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      session_date: new Date().toISOString().split('T')[0],
      client_id: '',
      duration_min: '60',
      fee_currency: 'TWD',
      fee_amount: '0',
      notes: ''
    });
  };

  const openCreateModal = async () => {
    resetForm();
    setShowModal(true);
    
    // Refresh clients list when opening modal
    try {
      const clientsData = await apiClient.getClients(1, 1000);
      setClients(clientsData.items || []);
    } catch (error) {
      console.error('Failed to refresh clients:', error);
      // Keep existing clients if refresh fails
    }
  };

  const fetchLastSessionData = async (clientId: string) => {
    if (!clientId) return;
    
    setLoadingLastSession(true);
    try {
      const lastSession = await apiClient.getClientLastSession(clientId);
      
      if (lastSession) {
        console.log('✅ Loading last session data for client:', clientId, lastSession);
        setFormData(prev => ({
          ...prev,
          duration_min: lastSession.duration_min.toString(),
          fee_currency: lastSession.fee_currency,
          fee_amount: lastSession.fee_amount.toString()
        }));
      } else {
        console.log('ℹ️ No previous session found for client:', clientId);
      }
    } catch (error) {
      console.error('❌ Failed to fetch last session data:', error);
      // Keep current values if fetch fails
    } finally {
      setLoadingLastSession(false);
    }
  };

  const handleClientCreated = async (newClient: Client) => {
    // Add new client to the list and select it
    setClients([...clients, newClient]);
    setFormData({ ...formData, client_id: newClient.id });
  };

  const handleViewDetails = (sessionId: string) => {
    router.push(`/dashboard/sessions/${sessionId}`);
  };

  if (loading && !sessions) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">{t('sessions.loading')}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-foreground">{t('sessions.title')}</h1>
        <Button onClick={openCreateModal} className="flex items-center gap-2">
          <PlusIcon className="h-5 w-5" />
          {t('sessions.addSession')}
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm mb-6 border border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('sessions.startDate')}</label>
            <Input
              type="date"
              value={filters.from_date}
              onChange={(e) => setFilters({ ...filters, from_date: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('sessions.endDate')}</label>
            <Input
              type="date"
              value={filters.to_date}
              onChange={(e) => setFilters({ ...filters, to_date: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('sessions.client')}</label>
            <Select
              value={filters.client_id}
              onChange={(e) => setFilters({ ...filters, client_id: e.target.value })}
            >
              <option value="">{t('sessions.allClients')}</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>
                  {client.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('sessions.currency')}</label>
            <Select
              value={filters.currency}
              onChange={(e) => setFilters({ ...filters, currency: e.target.value })}
            >
              <option value="">{t('sessions.allCurrencies')}</option>
              {currencies.map((currency) => (
                <option key={currency.value} value={currency.value}>
                  {String(currency.label || currency.value)}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('sessions.date')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('sessions.client')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('sessions.duration')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('sessions.fee')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('sessions.transcriptStatus')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('sessions.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {sessions?.map((session) => (
              <tr key={session.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {session.session_date}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={session.client.is_anonymized ? 'text-muted-foreground italic' : 'text-foreground'}>
                    {session.client.name}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {session.duration_display}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {session.fee_display}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getTranscriptionStatusBadge(session)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleViewDetails(session.id)}
                      className="text-blue-600 hover:text-blue-900"
                      title={t('sessions.viewDetails')}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => handleDelete(session)}
                      className="text-red-600 hover:text-red-900"
                      title={t('sessions.delete')}
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center mt-6">
          <div className="flex items-center gap-2">
            <Button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(currentPage - 1)}
              variant="outline"
            >
              {t('sessions.prevPage')}
            </Button>
            
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {t('sessions.page').replace('{current}', currentPage.toString()).replace('{total}', totalPages.toString())}
            </span>
            
            <Button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(currentPage + 1)}
              variant="outline"
            >
              {t('sessions.nextPage')}
            </Button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)}>
        <div className="bg-white dark:bg-gray-800 px-6 py-4 max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
          <h3 className="text-lg font-medium text-foreground mb-4">
            {t('sessions.newSession')}
          </h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('sessions.sessionDate')} *
                </label>
                <Input
                  type="date"
                  required
                  value={formData.session_date}
                  onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('sessions.client')} *
                  {loadingLastSession && (
                    <span className="ml-2 text-sm text-content-secondary">
                      ({t('sessions.loadingLastSession')}...)
                    </span>
                  )}
                </label>
                <Select
                  required
                  value={formData.client_id}
                  onChange={(e) => {
                    console.log('👤 Client selection changed:', e.target.value);
                    if (e.target.value === 'new') {
                      setShowClientModal(true);
                    } else {
                      setFormData({ ...formData, client_id: e.target.value });
                    }
                  }}
                >
                  <option value="">{t('sessions.selectClient')}</option>
                  <option value="new">+ {t('sessions.addNewClient')}</option>
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('sessions.durationMinutes')} *
              </label>
              <Input
                type="number"
                required
                min="1"
                value={formData.duration_min}
                onChange={(e) => setFormData({ ...formData, duration_min: e.target.value })}
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('sessions.currency')} *
                </label>
                <Select
                  value={formData.fee_currency}
                  onChange={(e) => setFormData({ ...formData, fee_currency: e.target.value })}
                >
                  {currencies.map((currency) => (
                    <option key={currency.value} value={currency.value}>
                      {String(currency.label || currency.value)}
                    </option>
                  ))}
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  {t('sessions.amount')} *
                </label>
                <Input
                  type="number"
                  min="0"
                  required
                  value={formData.fee_amount}
                  onChange={(e) => setFormData({ ...formData, fee_amount: e.target.value })}
                  placeholder="0"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('sessions.notes')}
              </label>
              <textarea
                className="w-full px-3 py-2 border border-border rounded-md bg-card text-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowModal(false)}
              >
                {t('common.cancel')}
              </Button>
              <Button type="submit">
                {t('sessions.create')}
              </Button>
            </div>
          </form>
        </div>
      </Modal>

      {/* Client Creation Modal */}
      <ClientModal
        isOpen={showClientModal}
        onClose={() => setShowClientModal(false)}
        onClientCreated={handleClientCreated}
      />
    </div>
  );
};

export default SessionsPage;