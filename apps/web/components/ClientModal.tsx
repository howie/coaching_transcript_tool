'use client';

import React, { useState } from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api';
import { useI18n } from '@/contexts/i18n-context';

interface ClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onClientCreated: (client: any) => void;
}

export const ClientModal: React.FC<ClientModalProps> = ({
  isOpen,
  onClose,
  onClientCreated
}) => {
  const { t } = useI18n();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    memo: ''
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const newClient = await apiClient.createClient(formData);
      onClientCreated(newClient);
      resetForm();
      onClose();
    } catch (error) {
      console.error('Failed to create client:', error);
      alert(t('clients.createError'));
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      email: '',
      phone: '',
      memo: ''
    });
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose}>
      <div className="bg-white px-6 py-4">
        <h3 className="text-lg font-medium mb-4">{t('clients.addClient')}</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('clients.name')} *
            </label>
            <Input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder={t('clients.namePlaceholder')}
              disabled={loading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('clients.email')}
            </label>
            <Input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder={t('clients.emailPlaceholder')}
              disabled={loading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('clients.phone')}
            </label>
            <Input
              type="tel"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder={t('clients.phonePlaceholder')}
              disabled={loading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('clients.memo')}
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              value={formData.memo}
              onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
              placeholder={t('clients.memoPlaceholder')}
              disabled={loading}
            />
          </div>
          
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? t('common.creating') : t('common.create')}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};