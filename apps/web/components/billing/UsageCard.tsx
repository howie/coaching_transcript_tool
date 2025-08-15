'use client'

import { UsageStatus } from '@/lib/services/plan.service';
import planService from '@/lib/services/plan.service';
import { 
  DocumentTextIcon, 
  ClockIcon, 
  MicrophoneIcon,
  CheckIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { useI18n } from '@/contexts/i18n-context';
import { useThemeClasses } from '@/lib/theme-utils';

interface UsageCardProps {
  usageStatus: UsageStatus;
  onUpgrade: () => void;
}

export function UsageCard({ usageStatus, onUpgrade }: UsageCardProps) {
  const { t } = useI18n();
  const themeClasses = useThemeClasses();
  
  const metrics = [
    {
      key: 'sessions',
      label: t('billing.sessions'),
      icon: DocumentTextIcon,
      current: usageStatus.currentUsage.sessions,
      limit: usageStatus.planLimits.maxSessions,
      percentage: usageStatus.usagePercentages.sessions,
      approaching: usageStatus.approachingLimits.sessions,
    },
    {
      key: 'minutes',
      label: t('billing.audioMinutes'),
      icon: ClockIcon,
      current: usageStatus.currentUsage.minutes,
      limit: usageStatus.planLimits.maxTotalMinutes,
      percentage: usageStatus.usagePercentages.minutes,
      approaching: usageStatus.approachingLimits.minutes,
    },
    {
      key: 'transcriptions',
      label: t('billing.transcriptions'),
      icon: MicrophoneIcon,
      current: usageStatus.currentUsage.transcriptions,
      limit: usageStatus.planLimits.maxTranscriptionCount,
      percentage: usageStatus.usagePercentages.transcriptions,
      approaching: usageStatus.approachingLimits.transcriptions,
    },
  ];

  const hasWarnings = Object.values(usageStatus.approachingLimits).some(v => v);

  return (
    <div className={themeClasses.card}>
      <div className="p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className={`text-xl font-semibold ${themeClasses.textPrimary}`}>
              {t('billing.currentUsage')}
            </h2>
          </div>
          {usageStatus.nextReset && (
            <div className="text-right">
              <p className={`text-xs ${themeClasses.textTertiary}`}>
                {t('billing.resetsIn')}
              </p>
              <p className={`text-sm font-medium ${themeClasses.textSecondary}`}>
                {planService.formatDaysUntil(usageStatus.nextReset)}
              </p>
            </div>
          )}
        </div>

        {hasWarnings && (
          <div className="mb-4 p-3 bg-yellow-500 bg-opacity-10 border border-yellow-500 border-opacity-30 rounded-lg">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-500">
                  {t('billing.approaching')}
                </p>
                <p className={`text-xs mt-1 ${themeClasses.textSecondary}`}>
                  {t('billing.considerUpgrading')}
                </p>
              </div>
              <button
                onClick={onUpgrade}
                className="ml-4 px-3 py-1 bg-yellow-500 bg-opacity-20 text-yellow-500 rounded text-sm font-medium hover:bg-opacity-30 transition-colors"
              >
                {t('billing.upgradeNow')}
              </button>
            </div>
          </div>
        )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {metrics.map((metric) => {
          const color = planService.getUsageColor(metric.percentage);
          const progressClass = planService.getProgressBarClass(metric.percentage);
          
          return (
            <div key={metric.key} className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <metric.icon className="h-5 w-5 text-dashboard-accent" />
                  <span className={`text-sm font-medium ${themeClasses.textPrimary}`}>
                    {metric.label}
                  </span>
                </div>
                {metric.percentage !== null && metric.percentage >= 90 && (
                  <span className="text-xs text-red-400 font-medium animate-pulse">
                    {metric.percentage}%
                  </span>
                )}
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className={`font-medium ${themeClasses.textPrimary}`}>
                    {metric.current.toLocaleString()}
                  </span>
                  <span className={themeClasses.textSecondary}>
                    / {planService.formatLimit(metric.limit)}
                  </span>
                </div>
                
                {metric.percentage !== null && (
                  <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div 
                      className={`h-2 rounded-full transition-all duration-500 ${progressClass}`}
                      style={{ width: `${Math.min(100, metric.percentage)}%` }}
                    />
                  </div>
                )}
                
                {metric.percentage === null && (
                  <div className="flex items-center space-x-1">
                    <CheckIcon className="h-4 w-4 text-green-500" />
                    <span className="text-xs text-green-500">{t('billing.unlimited')}</span>
                  </div>
                )}
              </div>
              
              {metric.approaching && metric.percentage !== null && (
                <p className="text-xs text-yellow-500">
                  {100 - metric.percentage}% {t('billing.remaining')}
                </p>
              )}
            </div>
          );
        })}
      </div>

        {usageStatus.upgradeSuggestion && (
          <div className="mt-6 p-4 bg-dashboard-accent bg-opacity-10 rounded-lg border border-dashboard-accent border-opacity-30">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-dashboard-accent mb-1">
                  {t('billing.upgradeTo')} {usageStatus.upgradeSuggestion.displayName}
                </h4>
                <p className={`text-xs mb-2 ${themeClasses.textSecondary}`}>
                  {usageStatus.upgradeSuggestion.tagline}
                </p>
                <ul className="space-y-1">
                  {usageStatus.upgradeSuggestion.keyBenefits.slice(0, 3).map((benefit, idx) => (
                    <li key={idx} className={`text-xs flex items-start ${themeClasses.textSecondary}`}>
                      <CheckIcon className="h-3 w-3 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <button
                onClick={onUpgrade}
                className={themeClasses.buttonPrimary + ' px-4 py-2 rounded-lg text-sm'}
              >
                {t('billing.upgradeNow')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}