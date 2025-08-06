'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { TagInput } from '@/components/ui/tag-input';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';

interface Client {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  memo?: string;
  source?: string;
  client_type?: string;
  issue_types?: string;
  is_anonymized: boolean;
}

interface ClientFormData {
  name: string;
  email: string;
  phone: string;
  memo: string;
  source: string;
  client_type: string;
  issue_types: string;
}

interface OptionItem {
  value: string;
  label: string;
}

const EditClientPage = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const params = useParams();
  const clientId = params.id as string;

  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [client, setClient] = useState<Client | null>(null);
  const [sourceOptions, setSourceOptions] = useState<OptionItem[]>([]);
  const [typeOptions, setTypeOptions] = useState<OptionItem[]>([]);
  const [formData, setFormData] = useState<ClientFormData>({
    name: '',
    email: '',
    phone: '',
    memo: '',
    source: '',
    client_type: '',
    issue_types: ''
  });

  useEffect(() => {
    if (clientId) {
      fetchClient();
      fetchOptions();
    }
  }, [clientId]);

  const fetchClient = async () => {
    try {
      const response = await fetch(`/api/v1/clients/${clientId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const clientData = await response.json();
        setClient(clientData);
        setFormData({
          name: clientData.name || '',
          email: clientData.email || '',
          phone: clientData.phone || '',
          memo: clientData.memo || '',
          source: clientData.source || '',
          client_type: clientData.client_type || '',
          issue_types: clientData.issue_types || ''
        });
      }
    } catch (error) {
      console.error('Failed to fetch client:', error);
    } finally {
      setFetching(false);
    }
  };

  const fetchOptions = async () => {
    try {
      const [sourcesRes, typesRes] = await Promise.all([
        fetch('/api/v1/clients/options/sources'),
        fetch('/api/v1/clients/options/types')
      ]);

      if (sourcesRes.ok) {
        const sourcesData = await sourcesRes.json();
        setSourceOptions(sourcesData);
      } else {
        console.error('Failed to fetch sources:', sourcesRes.status, sourcesRes.statusText);
      }

      if (typesRes.ok) {
        const typesData = await typesRes.json();
        setTypeOptions(typesData);
      } else {
        console.error('Failed to fetch types:', typesRes.status, typesRes.statusText);
      }
    } catch (error) {
      console.error('Failed to fetch options:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`/api/v1/clients/${clientId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        router.push('/dashboard/clients');
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Failed to update client:', response.status, errorData);
        alert(`更新客戶失敗: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to update client:', error);
    } finally {
      setLoading(false);
    }
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
        <div className="text-lg">Client not found</div>
      </div>
    );
  }

  if (client.is_anonymized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Cannot edit anonymized client</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">{t('clients.editClient')}</h1>
        </div>

        <div className="bg-white shadow-sm rounded-lg p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
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
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  客戶來源
                </label>
                <Select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                >
                  <option value="">請選擇來源</option>
                  {sourceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  客戶屬性
                </label>
                <Select
                  value={formData.client_type}
                  onChange={(e) => setFormData({ ...formData, client_type: e.target.value })}
                >
                  <option value="">請選擇屬性</option>
                  {typeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  議題類型
                </label>
                <TagInput
                  value={formData.issue_types}
                  onChange={(value) => setFormData({ ...formData, issue_types: value })}
                  placeholder="例如：職涯發展、人際關係、領導力"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('clients.memo')}
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
                value={formData.memo}
                onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                placeholder="備註資訊..."
              />
            </div>

            <div className="flex justify-end gap-4 pt-6 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push('/dashboard/clients')}
                disabled={loading}
              >
                {t('common.cancel')}
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? t('common.updating') : t('clients.update')}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditClientPage;