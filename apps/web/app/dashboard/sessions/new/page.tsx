'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

interface Client {
  id: string;
  name: string;
}

const NewSessionPage = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();
  const preSelectedClientId = searchParams.get('client_id');

  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState<Client[]>([]);
  const [currencies, setCurrencies] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    session_date: new Date().toISOString().split('T')[0],
    client_id: preSelectedClientId || '',
    duration_min: 60,
    fee_currency: 'TWD',
    fee_amount: 0,
    notes: ''
  });

  useEffect(() => {
    fetchClients();
    fetchCurrencies();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await apiClient.getClients(1, 100);
      setClients(response.items);
      
      // If pre-selected client, set it
      if (preSelectedClientId && response.items.some((c: Client) => c.id === preSelectedClientId)) {
        setFormData(prev => ({ ...prev, client_id: preSelectedClientId }));
      }
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
      // Fallback to default currencies
      setCurrencies([
        { value: 'TWD', label: 'TWD - 新台幣' },
        { value: 'USD', label: 'USD - 美元' },
        { value: 'CNY', label: 'CNY - 人民幣' }
      ]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.client_id) {
      alert(t('sessions.selectClient'));
      return;
    }

    setLoading(true);
    try {
      await apiClient.createSession({
        ...formData,
        fee_amount: Number(formData.fee_amount),
        duration_min: Number(formData.duration_min)
      });
      
      // Navigate back to sessions list or client detail
      if (preSelectedClientId) {
        router.push(`/dashboard/clients/${preSelectedClientId}/detail`);
      } else {
        router.push('/dashboard/sessions');
      }
    } catch (error) {
      console.error('Failed to create session:', error);
      alert(t('sessions.createError') || 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-content-primary">
            {t('sessions.newSession')}
          </h1>
        </div>

        <div className="bg-surface border border-border rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
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
                disabled={!!preSelectedClientId}
              >
                <option value="">{t('sessions.selectClient')}</option>
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
                placeholder={t('sessions.notesPlaceholder') || ''}
              />
            </div>

            <div className="flex justify-end gap-4 pt-6 border-t border-border">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  if (preSelectedClientId) {
                    router.push(`/dashboard/clients/${preSelectedClientId}/detail`);
                  } else {
                    router.push('/dashboard/sessions');
                  }
                }}
                disabled={loading}
              >
                {t('common.cancel')}
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? t('common.creating') : t('sessions.create')}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewSessionPage;