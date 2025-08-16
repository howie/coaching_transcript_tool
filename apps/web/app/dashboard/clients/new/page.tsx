'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { TagInput } from '@/components/ui/tag-input';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

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

const NewClientPage = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
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

  const fetchOptions = useCallback(async () => {
    try {
      const [sourcesData, typesData] = await Promise.all([
        apiClient.getClientSources(),
        apiClient.getClientTypes()
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

      setSourceOptions(processedSources);
      setTypeOptions(processedTypes);
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
    }
  }, [t]);

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]); // Use fetchOptions as dependency

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiClient.createClient(formData);
      router.push('/dashboard/clients');
    } catch (error) {
      console.error('Failed to create client:', error);
      alert(`${t('clients.createError')}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">{t('clients.newClient')}</h1>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('clients.clientSource')}
                </label>
                <Select
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                >
                  <option value="">{t('clients.selectSource')}</option>
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
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('clients.clientType')}
                </label>
                <Select
                  value={formData.client_type}
                  onChange={(e) => setFormData({ ...formData, client_type: e.target.value })}
                >
                  <option value="">{t('clients.selectType')}</option>
                  {typeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('clients.issueTypes')}
                </label>
                <TagInput
                  value={formData.issue_types}
                  onChange={(value) => setFormData({ ...formData, issue_types: value })}
                  placeholder={t('clients.issueTypesPlaceholder')}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('clients.memo')}
              </label>
              <textarea
                className="w-full px-3 py-2 border border-border rounded-md bg-card text-foreground placeholder:text-placeholder focus:outline-none focus:ring-2 focus:ring-accent"
                rows={4}
                value={formData.memo}
                onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
                placeholder={t('clients.memoPlaceholder')}
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
                {loading ? t('common.saving') : t('clients.create')}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default NewClientPage;