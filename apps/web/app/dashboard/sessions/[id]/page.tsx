'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { PencilIcon, TrashIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

interface Session {
  id: string;
  session_date: string;
  client_id: string;
  client_name?: string;
  duration_min: number;
  fee_currency: string;
  fee_amount: number;
  fee_display: string;
  duration_display: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface Client {
  id: string;
  name: string;
}

const SessionDetailPage = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const params = useParams();
  const sessionId = params.id as string;

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [editMode, setEditMode] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [clients, setClients] = useState<Client[]>([]);
  const [currencies, setCurrencies] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    session_date: '',
    client_id: '',
    duration_min: 60,
    fee_currency: 'TWD',
    fee_amount: 0,
    notes: ''
  });

  useEffect(() => {
    if (sessionId) {
      fetchSession();
      fetchClients();
      fetchCurrencies();
    }
  }, [sessionId]);

  const fetchSession = async () => {
    try {
      const data = await apiClient.getSession(sessionId);
      setSession(data);
      setFormData({
        session_date: data.session_date,
        client_id: data.client_id,
        duration_min: data.duration_min,
        fee_currency: data.fee_currency,
        fee_amount: data.fee_amount,
        notes: data.notes || ''
      });
    } catch (error) {
      console.error('Failed to fetch session:', error);
      setSession(null);
    } finally {
      setFetching(false);
    }
  };

  const fetchClients = async () => {
    try {
      const response = await apiClient.getClients(1, 100);
      setClients(response.items);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    }
  };

  const fetchCurrencies = async () => {
    try {
      const data = await apiClient.getCurrencies();
      setCurrencies(data);
    } catch (error) {
      console.error('Failed to fetch currencies:', error);
      setCurrencies([
        { value: 'TWD', label: 'TWD - 新台幣' },
        { value: 'USD', label: 'USD - 美元' },
        { value: 'CNY', label: 'CNY - 人民幣' }
      ]);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiClient.updateSession(sessionId, {
        ...formData,
        fee_amount: Number(formData.fee_amount),
        duration_min: Number(formData.duration_min)
      });
      setEditMode(false);
      fetchSession();
    } catch (error) {
      console.error('Failed to update session:', error);
      alert(t('sessions.updateError') || 'Failed to update session');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(t('sessions.confirmDelete'))) return;

    try {
      await apiClient.deleteSession(sessionId);
      router.push('/dashboard/sessions');
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert(t('sessions.deleteError') || 'Failed to delete session');
    }
  };

  if (fetching) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">{t('sessions.loading')}</div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Session not found</div>
      </div>
    );
  }

  const currentClient = clients.find(c => c.id === session.client_id);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-content-primary">
            {t('sessions.sessionDetail')}
          </h1>
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => router.push('/dashboard/sessions')}
              className="flex items-center gap-2"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              {t('common.back')}
            </Button>
            {!editMode ? (
              <Button
                onClick={() => setEditMode(true)}
                className="flex items-center gap-2"
              >
                <PencilIcon className="h-4 w-4" />
                {t('common.edit')}
              </Button>
            ) : null}
            <Button
              variant="outline"
              onClick={handleDelete}
              className="flex items-center gap-2 text-red-600 hover:text-red-700"
            >
              <TrashIcon className="h-4 w-4" />
              {t('common.delete')}
            </Button>
          </div>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          {editMode ? (
            <form onSubmit={handleUpdate} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-content-primary mb-2">
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
                <label className="block text-sm font-medium text-content-primary mb-2">
                  {t('sessions.client')} *
                </label>
                <Select
                  required
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                >
                  {clients.map((client) => (
                    <option key={client.id} value={client.id}>
                      {client.name}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-content-primary mb-2">
                  {t('sessions.durationMinutes')}
                </label>
                <Input
                  type="number"
                  min="1"
                  required
                  value={formData.duration_min}
                  onChange={(e) => setFormData({ ...formData, duration_min: parseInt(e.target.value) || 0 })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('sessions.currency')}
                  </label>
                  <Select
                    value={formData.fee_currency}
                    onChange={(e) => setFormData({ ...formData, fee_currency: e.target.value })}
                  >
                    {currencies.map((currency) => (
                      <option key={currency.value} value={currency.value}>
                        {currency.label}
                      </option>
                    ))}
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-primary mb-2">
                    {t('sessions.amount')} *
                  </label>
                  <Input
                    type="number"
                    min="0"
                    required
                    value={formData.fee_amount}
                    onChange={(e) => setFormData({ ...formData, fee_amount: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-content-primary mb-2">
                  {t('sessions.notes')}
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-border rounded-md bg-surface text-content-primary focus:outline-none focus:ring-2 focus:ring-accent"
                  rows={4}
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-4 pt-6 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setEditMode(false);
                    // Reset form data
                    setFormData({
                      session_date: session.session_date,
                      client_id: session.client_id,
                      duration_min: session.duration_min,
                      fee_currency: session.fee_currency,
                      fee_amount: session.fee_amount,
                      notes: session.notes || ''
                    });
                  }}
                  disabled={loading}
                >
                  {t('common.cancel')}
                </Button>
                <Button type="submit" disabled={loading}>
                  {loading ? t('common.updating') : t('common.save')}
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('sessions.sessionDate')}
                  </label>
                  <p className="text-content-primary text-lg">{session.session_date}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('sessions.client')}
                  </label>
                  <p className="text-content-primary text-lg">
                    {currentClient?.name || session.client_name || '-'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('sessions.duration')}
                  </label>
                  <p className="text-content-primary">{session.duration_display}</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('sessions.fee')}
                  </label>
                  <p className="text-content-primary text-lg font-medium">{session.fee_display}</p>
                </div>
              </div>

              {session.notes && (
                <div>
                  <label className="block text-sm font-medium text-content-secondary mb-1">
                    {t('sessions.notes')}
                  </label>
                  <p className="text-content-primary whitespace-pre-wrap">{session.notes}</p>
                </div>
              )}

              <div className="pt-4 border-t border-border">
                <div className="text-sm text-content-secondary">
                  <p>{t('common.createdAt')}: {new Date(session.created_at).toLocaleString()}</p>
                  <p>{t('common.updatedAt')}: {new Date(session.updated_at).toLocaleString()}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SessionDetailPage;