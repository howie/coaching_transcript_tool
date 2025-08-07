'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PlusIcon, PencilIcon, TrashIcon, UserMinusIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

interface Client {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  memo?: string;
  is_anonymized: boolean;
  anonymized_at?: string;
  session_count: number;
  created_at: string;
  updated_at: string;
}

const ClientsPage = () => {
  const { user } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchClients();
  }, [currentPage, searchQuery]);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getClients(currentPage, pageSize, searchQuery);
      setClients(data.items);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('Failed to fetch clients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (client: Client) => {
    router.push(`/dashboard/clients/${client.id}/edit`);
  };

  const handleDelete = async (client: Client) => {
    if (!confirm(t('clients.confirmDelete').replace('{name}', client.name))) return;

    try {
      await apiClient.deleteClient(client.id);
      fetchClients();
    } catch (error) {
      console.error('Failed to delete client:', error);
      if (error instanceof Error && error.message.includes('existing sessions')) {
        alert(t('clients.deleteError'));
      }
    }
  };

  const handleAnonymize = async (client: Client) => {
    if (!confirm(t('clients.confirmAnonymize').replace('{name}', client.name))) return;

    try {
      await apiClient.anonymizeClient(client.id);
      fetchClients();
    } catch (error) {
      console.error('Failed to anonymize client:', error);
    }
  };

  const handleCreate = () => {
    router.push('/dashboard/clients/new');
  };

  if (loading && clients.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">{t('clients.loading')}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-white">{t('clients.title')}</h1>
        <Button onClick={handleCreate} className="flex items-center gap-2">
          <PlusIcon className="h-5 w-5" />
          {t('clients.addClient')}
        </Button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <Input
          type="text"
          placeholder={t('clients.search')}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-md"
        />
      </div>

      {/* Clients Table */}
      <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.name')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.email')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.phone')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.sessions')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.status')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.actions')}
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {clients.map((client) => (
              <tr key={client.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={client.is_anonymized ? 'text-muted-foreground italic' : 'text-foreground'}>
                    {client.name}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {client.email || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {client.phone || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {client.session_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {client.is_anonymized ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                      {t('clients.anonymized')}
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                      {t('clients.normal')}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex items-center gap-2">
                    {!client.is_anonymized && (
                      <button
                        onClick={() => handleEdit(client)}
                        className="text-indigo-600 hover:text-indigo-900"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                    )}
                    
                    {client.session_count === 0 ? (
                      <button
                        onClick={() => handleDelete(client)}
                        className="text-red-600 hover:text-red-900"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    ) : !client.is_anonymized ? (
                      <button
                        onClick={() => handleAnonymize(client)}
                        className="text-orange-600 hover:text-orange-900"
                        title="匿名化"
                      >
                        <UserMinusIcon className="h-4 w-4" />
                      </button>
                    ) : null}
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
              {t('clients.prevPage')}
            </Button>
            
            <span className="text-sm text-gray-700 dark:text-gray-300">
              {t('clients.page').replace('{current}', currentPage.toString()).replace('{total}', totalPages.toString())}
            </span>
            
            <Button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(currentPage + 1)}
              variant="outline"
            >
              {t('clients.nextPage')}
            </Button>
          </div>
        </div>
      )}

    </div>
  );
};

export default ClientsPage;