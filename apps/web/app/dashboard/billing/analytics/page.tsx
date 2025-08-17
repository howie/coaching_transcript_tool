'use client';

import React from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import UsageHistory from '@/components/billing/UsageHistory';

export default function BillingAnalyticsPage() {
  const { user } = useAuth();
  const { t } = useI18n();

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-content-primary mb-4">
            {t('auth.signInRequired')}
          </h2>
          <p className="text-content-secondary">
            {t('auth.pleaseSignInToAccess')} {t('analytics.usageHistory').toLowerCase()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dashboard-background">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Page Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-content-primary">
                  {t('analytics.usageHistory')}
                </h1>
                <p className="mt-2 text-content-secondary">
                  {t('billing.trackYourUsagePatterns')}
                </p>
              </div>
              
              {/* Quick Stats Summary */}
              <div className="hidden lg:flex items-center space-x-6 text-sm">
                <div className="text-center">
                  <div className="text-content-secondary">{t('billing.currentPlan')}</div>
                  <div className="font-semibold text-content-primary">{user.plan?.toUpperCase() || 'FREE'}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Usage History Component */}
          <UsageHistory 
            userId={user.id}
            defaultPeriod="30d"
            showInsights={true}
            showPredictions={true}
          />

          {/* Additional Information */}
          <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Data Retention Notice */}
            <div className="bg-dashboard-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-content-primary mb-3 flex items-center">
                <span className="mr-2">📋</span>
                {t('analytics.dataRetention')}
              </h3>
              <div className="space-y-2 text-sm text-content-secondary">
                <p>{t('analytics.dataRetentionDescription')}</p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>{t('analytics.dailyDataRetained')}</li>
                  <li>{t('analytics.monthlyDataRetained')}</li>
                  <li>{t('analytics.exportDataAnytime')}</li>
                </ul>
              </div>
            </div>

            {/* Privacy and Security */}
            <div className="bg-dashboard-card border border-border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-content-primary mb-3 flex items-center">
                <span className="mr-2">🔒</span>
                {t('analytics.privacySecurity')}
              </h3>
              <div className="space-y-2 text-sm text-content-secondary">
                <p>{t('analytics.privacyDescription')}</p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>{t('analytics.encryptedStorage')}</li>
                  <li>{t('analytics.gdprCompliant')}</li>
                  <li>{t('analytics.userControlledData')}</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Help and Support */}
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <span className="text-2xl">💡</span>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-blue-900">
                  {t('analytics.needHelp')}
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>{t('analytics.helpDescription')}</p>
                  <div className="mt-3 flex space-x-4">
                    <a
                      href="/help/analytics"
                      className="font-medium text-blue-800 hover:text-blue-600"
                    >
                      {t('help.viewGuide')} →
                    </a>
                    <a
                      href="/help/contact"
                      className="font-medium text-blue-800 hover:text-blue-600"
                    >
                      {t('help.contactSupport')} →
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}