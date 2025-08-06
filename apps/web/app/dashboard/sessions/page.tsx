'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PlusIcon, PencilIcon, TrashIcon, DocumentTextIcon, MicrophoneIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Modal } from '@/components/ui/modal';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';

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
  transcript_timeseq_id?: string;
  audio_timeseq_id?: string;
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
  const { user } = useAuth();
  const { t } = useI18n();
  const [sessions, setSessions] = useState<CoachingSession[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [currencies, setCurrencies] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSession, setEditingSession] = useState<CoachingSession | null>(null);
  const [formData, setFormData] = useState<SessionFormData>({
    session_date: '',
    client_id: '',
    duration_min: '',
    fee_currency: 'NTD',
    fee_amount: '',
    notes: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    from_date: '',
    to_date: '',
    client_id: '',
    currency: ''
  });
  const pageSize = 20;

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [currentPage, filters]);

  const fetchInitialData = async () => {
    try {
      const [clientsRes, currenciesRes] = await Promise.all([
        fetch('/api/v1/clients?page_size=1000', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/sessions/options/currencies')
      ]);

      if (clientsRes.ok) {
        const clientsData = await clientsRes.json();
        setClients(clientsData.items);
      }

      if (currenciesRes.ok) {
        const currenciesData = await currenciesRes.json();
        setCurrencies(currenciesData);
      }
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
    }
  };

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        sort: '-session_date'
      });

      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });

      const response = await fetch(`/api/v1/sessions?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSessions(data.items);
        setTotalPages(data.total_pages);
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        duration_min: parseInt(formData.duration_min),
        fee_amount: parseInt(formData.fee_amount)
      };

      const url = editingSession 
        ? `/api/v1/sessions/${editingSession.id}`
        : '/api/v1/sessions';
      
      const method = editingSession ? 'PATCH' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setShowModal(false);
        setEditingSession(null);
        resetForm();
        fetchSessions();
      }
    } catch (error) {
      console.error('Failed to save session:', error);
    }
  };

  const handleEdit = (session: CoachingSession) => {
    setEditingSession(session);
    setFormData({
      session_date: session.session_date,
      client_id: session.client.id,
      duration_min: session.duration_min.toString(),
      fee_currency: session.fee_currency,
      fee_amount: session.fee_amount.toString(),
      notes: session.notes || ''
    });
    setShowModal(true);
  };

  const handleDelete = async (session: CoachingSession) => {
    if (!confirm(t('sessions.confirmDelete'))) return;

    try {
      const response = await fetch(`/api/v1/sessions/${session.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        fetchSessions();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      session_date: '',
      client_id: '',
      duration_min: '',
      fee_currency: 'NTD',
      fee_amount: '',
      notes: ''
    });
  };

  const openCreateModal = () => {
    setEditingSession(null);
    resetForm();
    setShowModal(true);
  };

  const handleUploadTranscript = (sessionId: string) => {
    window.location.href = `/dashboard/transcript-converter?session_id=${sessionId}`;
  };

  if (loading && sessions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">{t('sessions.loading')}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">{t('sessions.title')}</h1>
        <Button onClick={openCreateModal} className="flex items-center gap-2">
          <PlusIcon className="h-5 w-5" />
          {t('sessions.addSession')}
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('sessions.startDate')}</label>
            <Input
              type="date"
              value={filters.from_date}
              onChange={(e) => setFilters({ ...filters, from_date: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('sessions.endDate')}</label>
            <Input
              type="date"
              value={filters.to_date}
              onChange={(e) => setFilters({ ...filters, to_date: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('sessions.client')}</label>
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
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('sessions.currency')}</label>
            <Select
              value={filters.currency}
              onChange={(e) => setFilters({ ...filters, currency: e.target.value })}
            >
              <option value="">{t('sessions.allCurrencies')}</option>
              {currencies.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </div>

      {/* Sessions Table */}
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('sessions.date')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('sessions.client')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('sessions.duration')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('sessions.fee')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {t('sessions.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sessions.map((session) => (
              <tr key={session.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {session.session_date}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={session.client.is_anonymized ? 'text-gray-400 italic' : ''}>
                    {session.client.name}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {session.duration_display}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {session.fee_display}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(session)}
                      className="text-indigo-600 hover:text-indigo-900"
                      title="編輯"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => handleDelete(session)}
                      className="text-red-600 hover:text-red-900"
                      title="刪除"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => handleUploadTranscript(session.id)}
                      className="text-green-600 hover:text-green-900"
                      title="上傳逐字稿"
                    >
                      <DocumentTextIcon className="h-4 w-4" />
                    </button>
                    
                    <button
                      onClick={() => console.log('Upload audio for', session.id)}
                      className="text-blue-600 hover:text-blue-900"
                      title="上傳錄音檔"
                    >
                      <MicrophoneIcon className="h-4 w-4" />
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
            
            <span className="text-sm text-gray-700">
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

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)}>
        <div className="bg-white px-6 py-4 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-lg font-medium mb-4">
            {editingSession ? t('sessions.editSession') : t('sessions.newSession')}
          </h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('sessions.client')} *
                </label>
                <Select
                  required
                  value={formData.client_id}
                  onChange={(e) => {
                    if (e.target.value === 'new') {
                      setShowModal(false);
                      router.push('/dashboard/clients/new');
                    } else {
                      setFormData({ ...formData, client_id: e.target.value });
                    }
                  }}
                >
                  <option value="">{t('sessions.selectClient')}</option>
                  <option value="new">+ 新增客戶</option>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('sessions.currency')} *
                </label>
                <Select
                  value={formData.fee_currency}
                  onChange={(e) => setFormData({ ...formData, fee_currency: e.target.value })}
                >
                  {currencies.map((currency) => (
                    <option key={currency} value={currency}>
                      {currency}
                    </option>
                  ))}
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('sessions.amount')} *
                </label>
                <Input
                  type="number"
                  required
                  min="0"
                  value={formData.fee_amount}
                  onChange={(e) => setFormData({ ...formData, fee_amount: e.target.value })}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('sessions.notes')}
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                {editingSession ? t('sessions.update') : t('sessions.create')}
              </Button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
};

export default SessionsPage;