'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PlusIcon, PencilIcon, TrashIcon, UserMinusIcon } from '@heroicons/react/24/outline';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';
import PieChart from '@/components/charts/PieChart';

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
  anonymized_at?: string;
  session_count: number;
  total_payment_amount: number;
  total_payment_currency: string;
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
  const [statistics, setStatistics] = useState<any>(null);
  const pageSize = 20;

  const getStatusLabel = (status: string) => {
    const statusMap = {
      'first_session': '首次會談',
      'in_progress': '進行中',
      'paused': '暫停',
      'completed': '結案'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  // Translation helpers
  const getSourceLabel = (value: string | null | undefined) => {
    if (!value) return '-';
    const sourceLabels: Record<string, string> = {
      'referral': '別人推薦',
      'organic': '自然搜尋',
      'friend': '朋友介紹',
      'social_media': '社群媒體',
      'advertisement': '廣告',
      'website': '官方網站',
      'unknown': '未知'
    };
    return sourceLabels[value] || value;
  };

  const getTypeLabel = (value: string | null | undefined) => {
    if (!value) return '-';
    const typeLabels: Record<string, string> = {
      'paid': '付費客戶',
      'pro_bono': '公益服務',
      'free_practice': '免費練習',
      'other': '其他',
      'unknown': '未知'
    };
    return typeLabels[value] || value;
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

  useEffect(() => {
    fetchClients();
    fetchStatistics();
  }, [currentPage, searchQuery]);

  const fetchStatistics = async () => {
    try {
      console.log('Fetching client statistics...');
      const stats = await apiClient.getClientStatistics();
      console.log('Statistics received:', stats);
      setStatistics(stats);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };

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

  const handleDetail = (client: Client) => {
    router.push(`/dashboard/clients/${client.id}/detail`);
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
        <h1 className="text-3xl font-bold text-content-primary">{t('clients.title')}</h1>
        <Button onClick={handleCreate} className="flex items-center gap-2">
          <PlusIcon className="h-5 w-5" />
          {t('clients.addClient')}
        </Button>
      </div>

      {/* Statistics Charts */}
      <div className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <PieChart
            data={statistics?.source_distribution || []}
            title={t('clients.chartSourceTitle')}
            width={250}
            height={200}
          />
          <PieChart
            data={statistics?.type_distribution || []}
            title={t('clients.chartTypeTitle')}
            width={250}
            height={200}
          />
          <PieChart
            data={statistics?.issue_distribution || []}
            title={t('clients.chartIssueTitle')}
            width={250}
            height={200}
          />
        </div>
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
                {t('clients.clientSource')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.clientType')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                議題類型
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.sessions')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                {t('clients.totalPayment')}
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
                  <button
                    onClick={() => handleDetail(client)}
                    className={`text-left hover:underline ${client.is_anonymized ? 'text-muted-foreground italic' : 'text-foreground hover:text-accent'}`}
                  >
                    {client.name}
                  </button>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {client.email || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {getSourceLabel(client.source)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {getTypeLabel(client.client_type)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  <div className="flex flex-wrap gap-1 max-w-xs">
                    {client.issue_types ? 
                      client.issue_types.split(',').slice(0, 2).map((issue, index) => (
                        <span 
                          key={index}
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200"
                          title={issue.trim()}
                        >
                          {issue.trim().length > 10 ? `${issue.trim().substring(0, 10)}...` : issue.trim()}
                        </span>
                      )) : 
                      '-'
                    }
                    {client.issue_types && client.issue_types.split(',').length > 2 && (
                      <span className="text-xs text-content-secondary">
                        +{client.issue_types.split(',').length - 2}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {client.session_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground">
                  {client.total_payment_currency} {client.total_payment_amount.toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {client.is_anonymized ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                      {t('clients.anonymized')}
                    </span>
                  ) : (
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(client.status)}`}>
                      {getStatusLabel(client.status)}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex items-center gap-2">
                    {!client.is_anonymized && (
                      <button
                        onClick={() => handleDetail(client)}
                        className="text-indigo-600 hover:text-indigo-900"
                        title="檢視詳情"
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

      {/* 刪除與匿名化規則說明 */}
      <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
          客戶資料管理規則
        </h3>
        <div className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
          <div className="flex items-start gap-2">
            <TrashIcon className="h-4 w-4 mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400" />
            <div>
              <span className="font-medium">直接刪除：</span>
              <span className="ml-1">僅適用於沒有任何教練會話記錄的客戶。刪除後資料將永久移除且無法復原。</span>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <UserMinusIcon className="h-4 w-4 mt-0.5 flex-shrink-0 text-orange-600 dark:text-orange-400" />
            <div>
              <span className="font-medium">匿名化：</span>
              <span className="ml-1">適用於已有教練會話記錄的客戶。匿名化會保留會話記錄但移除所有個人識別資訊（姓名、電話、Email、備註），符合 GDPR 隱私保護規範。</span>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-gray-600 dark:text-gray-400 mt-0.5">•</span>
            <div>
              <span className="font-medium">已匿名化：</span>
              <span className="ml-1">已匿名化的客戶無法編輯或刪除，僅能查看歷史會話記錄。</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};

export default ClientsPage;