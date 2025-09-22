'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PencilIcon, PlusIcon, EyeIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { TagInput } from '@/components/ui/tag-input';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

interface Client {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  memo?: string;
  source?: string;
  client_type?: string;
  issue_types?: string;
  status: string;
  is_anonymized: boolean;
  created_at: string;
  updated_at: string;
  session_count: number;
  total_payment_amount: number;
  total_payment_currency: string;
}

interface CoachingSession {
  id: string;
  session_date: string;
  duration_min: number;
  fee_currency: string;
  fee_amount: number;
  fee_display: string;
  duration_display: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface ClientFormData {
  name: string;
  email: string;
  phone: string;
  memo: string;
  source: string;
  client_type: string;
  issue_types: string;
  status: string;
}

interface OptionItem {
  value: string;
  label?: string;
  labelKey?: string;
}

const ClientDetailPage = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const params = useParams();
  const clientId = params.id as string;

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [client, setClient] = useState<Client | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<CoachingSession[]>([]);
  const [sourceOptions, setSourceOptions] = useState<OptionItem[]>([]);
  const [typeOptions, setTypeOptions] = useState<OptionItem[]>([]);
  const [statusOptions, setStatusOptions] = useState<OptionItem[]>([]);
  const [formData, setFormData] = useState<ClientFormData>({
    name: '',
    email: '',
    phone: '',
    memo: '',
    source: '',
    client_type: '',
    issue_types: '',
    status: ''
  });

  const fetchOptions = useCallback(async () => {
    try {
      const [sourcesData, typesData, statusesData] = await Promise.all([
        apiClient.getClientSources(),
        apiClient.getClientTypes(),
        apiClient.getClientStatuses()
      ]);

      // Convert labelKey to label using i18n
      const processedSources = sourcesData.map((item: any) => ({
        value: item.value,
        label: item.labelKey ? t(item.labelKey) : item.label || item.value
      }));

      const processedTypes = typesData.map((item: any) => ({
        value: item.value,
        label: item.labelKey ? t(item.labelKey) : item.label || item.value
      }));

      const processedStatuses = statusesData.map((item: any) => ({
        value: item.value,
        label: item.labelKey ? t(item.labelKey) : item.label || item.value
      }));

      setSourceOptions(processedSources);
      setTypeOptions(processedTypes);
      setStatusOptions(processedStatuses);
    } catch (error) {
      console.error('Failed to fetch options:', error);
      // Set default options when API fails
      setSourceOptions([
        { value: 'referral', label: t('clients.sourceReferral') },
        { value: 'website', label: t('clients.sourceWebsite') },
        { value: 'social_media', label: t('clients.sourceSocialMedia') },
        { value: 'event', label: t('clients.sourceEvent') },
        { value: 'other', label: t('clients.sourceOther') }
      ]);
      setTypeOptions([
        { value: 'individual', label: t('clients.typeIndividual') },
        { value: 'corporate', label: t('clients.typeCorporate') },
        { value: 'student', label: t('clients.typeStudent') },
        { value: 'professional', label: t('clients.typeProfessional') },
        { value: 'other', label: t('clients.typeOther') }
      ]);
      setStatusOptions([
        { value: 'first_session', label: t('clients.statusFirstSession') },
        { value: 'active', label: t('clients.statusInProgress') },
        { value: 'paused', label: t('clients.statusPaused') },
        { value: 'completed', label: t('clients.statusCompleted') }
      ]);
    }
  }, [t]);

  const fetchClient = useCallback(async () => {
    try {
      console.log('Fetching client with ID:', clientId);
      const clientData = await apiClient.getClient(clientId);
      console.log('Client data received:', clientData);
      setClient(clientData);
      setFormData({
        name: clientData.name || '',
        email: clientData.email || '',
        phone: clientData.phone || '',
        memo: clientData.memo || '',
        source: clientData.source || '',
        client_type: clientData.client_type || '',
        issue_types: clientData.issue_types || '',
        status: clientData.status || 'first_session'
      });
    } catch (error) {
      console.error('Failed to fetch client:', error);
      console.error('Client ID:', clientId);
      console.error('Error details:', error);
      setClient(null);
      setError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setFetching(false);
    }
  }, [clientId]);

  const fetchSessions = useCallback(async () => {
    try {
      const sessionsData = await apiClient.getSessions(1, 50, { client_id: clientId });
      setSessions(sessionsData.items || []);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      setSessions([]);
    }
  }, [clientId]);

  useEffect(() => {
    if (clientId) {
      fetchClient();
      fetchSessions();
      fetchOptions();
    }
  }, [clientId, fetchClient, fetchSessions, fetchOptions]);

  const getStatusLabel = (status: string) => {
    const statusMap = {
      'first_session': t('clients.statusFirstSession'),
      'in_progress': t('clients.statusInProgress'),
      'paused': t('clients.statusPaused'),
      'completed': t('clients.statusCompleted')
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  const getStatusColor = (status: string) => {
    const colorMap = {
      'first_session': 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
      'in_progress': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
      'paused': 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
      'completed': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
    };
    return colorMap[status as keyof typeof colorMap] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
  };


  // Translation helpers
  const getSourceLabel = (value: string | null | undefined) => {
    if (!value) return '-';
    const sourceLabels: Record<string, string> = {
      'referral': t('clients.sourceReferral'),
      'organic': t('clients.sourceOrganic'),
      'friend': t('clients.sourceFriend'),
      'social_media': t('clients.sourceSocialMedia'),
      'advertisement': t('clients.sourceAdvertisement'),
      'website': t('clients.sourceWebsite'),
      'unknown': t('clients.sourceUnknown')
    };
    return sourceLabels[value] || value;
  };

  const getTypeLabel = (value: string | null | undefined) => {
    if (!value) return '-';
    const typeLabels: Record<string, string> = {
      'paid': t('clients.typePaid'),
      'pro_bono': t('clients.typeProBono'),
      'free_practice': t('clients.typeFreePractice'),
      'other': t('clients.typeOther'),
      'unknown': t('clients.typeUnknown')
    };
    return typeLabels[value] || value;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiClient.updateClient(clientId, formData);
      setEditMode(false);
      fetchClient(); // Refresh data
    } catch (error) {
      console.error('Failed to update client:', error);
      alert(`${t('clients.updateError')}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionClick = (sessionId: string) => {
    router.push(`/dashboard/sessions/${sessionId}`);
  };

  const handleNewSession = () => {
    router.push(`/dashboard/sessions/new?client_id=${clientId}`);
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">{t('clients.loading')}</div>
      </div>
    );
  }

  if (!client) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-lg mb-2">Client not found</div>
          {error && <div className="text-sm text-red-600">Error: {error}</div>}
          <div className="text-sm text-gray-500 mt-2">Client ID: {clientId}</div>
        </div>
      </div>
    );
  }

  if (client.is_anonymized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Cannot view anonymized client</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-content-primary">{t('clients.detailTitle')}</h1>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard/clients')}
            >
              {t('common.back')}
            </Button>
            {!editMode ? (
              <Button
                onClick={() => setEditMode(true)}
                className="flex items-center gap-2"
              >
                <PencilIcon className="h-4 w-4" />
                {t('clients.editMode')}
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => {
                  setEditMode(false);
                  // Reset form data to original values
                  setFormData({
                    name: client.name || '',
                    email: client.email || '',
                    phone: client.phone || '',
                    memo: client.memo || '',
                    source: client.source || '',
                    client_type: client.client_type || '',
                    issue_types: client.issue_types || '',
                    status: client.status || 'first_session'
                  });
                }}
                className="flex items-center gap-2"
              >
                <EyeIcon className="h-4 w-4" />
                {t('clients.viewMode')}
              </Button>
            )}
          </div>
        </div>

        {/* Client Information */}
        <div className="bg-surface border border-border rounded-lg p-6 mb-8">
          {editMode ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('clients.name')} *
                  </label>
                  <Input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder={t('clients.namePlaceholder')}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('clients.email')}
                  </label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder={t('clients.emailPlaceholder')}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('clients.phone')}
                  </label>
                  <Input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder={t('clients.phonePlaceholder')}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('clients.clientSource')}
                  </label>
                  <Select
                    value={formData.source}
                    onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  >
                    <option value="">{t('clients.selectSource')}</option>
                    {sourceOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.labelKey ? t(option.labelKey as any) : option.label}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('clients.clientType')}
                  </label>
                  <Select
                    value={formData.client_type}
                    onChange={(e) => setFormData({ ...formData, client_type: e.target.value })}
                  >
                    <option value="">{t('clients.selectType')}</option>
                    {typeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.labelKey ? t(option.labelKey as any) : option.label}
                      </option>
                    ))}
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('clients.issueTypes')}
                  </label>
                  <TagInput
                    value={formData.issue_types}
                    onChange={(value) => setFormData({ ...formData, issue_types: value })}
                    placeholder={t('clients.issueTypesPlaceholder')}
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-content-primary mb-2">
                  {t('clients.clientStatus')} *
                </label>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  required
                >
                  <option value="">{t('clients.selectStatus')}</option>
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.labelKey ? t(option.labelKey as any) : option.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-content-primary mb-2">
                  {t('clients.memo')}
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-border rounded-md bg-surface text-content-primary focus:outline-none focus:ring-2 focus:ring-accent"
                  rows={4}
                  value={formData.memo}
                  onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                  placeholder={t('clients.memoPlaceholder')}
                />
              </div>

              <div className="flex justify-end gap-4 pt-6 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditMode(false)}
                  disabled={loading}
                >
                  {t('common.cancel')}
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? t('common.updating') : t('clients.update')}
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.name')}
                  </label>
                  <p className="text-content-primary text-lg font-medium">{client.name}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.clientStatus')}
                  </label>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${getStatusColor(client.status)}`}>
                    {getStatusLabel(client.status)}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.sessionCount')}
                  </label>
                  <p className="text-content-primary">{client.session_count} {t('clients.times')}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.totalPayment')}
                  </label>
                  <p className="text-content-primary text-lg font-medium">
                    {client.total_payment_currency} {client.total_payment_amount.toLocaleString()}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.email')}
                  </label>
                  <p className="text-content-primary">{client.email || '-'}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.phone')}
                  </label>
                  <p className="text-content-primary">{client.phone || '-'}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.clientSource')}
                  </label>
                  <p className="text-content-primary">{getSourceLabel(client.source)}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.clientType')}
                  </label>
                  <p className="text-content-primary">{getTypeLabel(client.client_type)}</p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-content-secondary mb-1">
                  {t('clients.issueTypes')}
                </label>
                <div className="flex flex-wrap gap-2">
                  {client.issue_types ? 
                    client.issue_types.split(',').map((issue, index) => (
                      <span 
                        key={index}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                      >
                        {issue.trim()}
                      </span>
                    )) : 
                    <span className="text-content-secondary">-</span>
                  }
                </div>
              </div>

              {client.memo && (
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('clients.memo')}
                  </label>
                  <p className="text-content-primary whitespace-pre-wrap">{client.memo}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sessions List */}
        <div className="bg-surface border border-border rounded-lg">
          <div className="p-6 border-b border-border">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-content-primary">{t('clients.sessionList')}</h2>
              <Button
                onClick={handleNewSession}
                className="flex items-center gap-2"
              >
                <PlusIcon className="h-4 w-4" />
                {t('clients.addSession')}
              </Button>
            </div>
          </div>

          {sessions.length === 0 ? (
            <div className="p-6 text-center text-content-secondary">
              {t('clients.noSessions')}
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-border">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider">
                      {t('clients.sessionDate')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider">
                      {t('sessions.duration')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider">
                      {t('sessions.fee')}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-content-secondary uppercase tracking-wider">
                      {t('sessions.actions')}
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-surface divide-y divide-border">
                  {sessions.map((session) => (
                    <tr key={session.id} className="hover:bg-muted/50 cursor-pointer" onClick={() => handleSessionClick(session.id)}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-content-primary">
                        {session.session_date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-content-primary">
                        {session.duration_display}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-content-primary">
                        {session.fee_display}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleSessionClick(session.id);
                          }}
                          className="text-accent hover:text-accent/80"
                          title={t('clients.viewDetails')}
                        >
                          <DocumentTextIcon className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClientDetailPage;