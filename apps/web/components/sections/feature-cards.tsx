'use client'

import Link from 'next/link'
import { useI18n } from '@/contexts/i18n-context'

interface FeatureCardProps {
  title: string
  description: string
  buttonText: string
  href: string
  comingSoon?: boolean
}

function FeatureCard({ title, description, buttonText, href, comingSoon }: FeatureCardProps) {
  if (comingSoon) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 shadow-sm opacity-60">
        <h3 className="text-lg font-semibold text-foreground mb-3">
          {title}
        </h3>
        <p className="text-muted-foreground mb-4 text-sm leading-relaxed">
          {description}
        </p>
        <div className="pt-2">
          <span className="inline-flex items-center px-3 py-2 border border-border text-sm font-medium rounded-md text-muted-foreground cursor-not-allowed">
            {buttonText}
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="text-lg font-semibold text-foreground mb-3">
        {title}
      </h3>
      <p className="text-muted-foreground mb-4 text-sm leading-relaxed">
        {description}
      </p>
      <div className="pt-2">
        <Link
          href={href as any}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-dashboard-accent hover:bg-dashboard-accent-dark transition-colors"
        >
          {buttonText}
        </Link>
      </div>
    </div>
  )
}

export function FeatureCards() {
  const { t } = useI18n()

  const features = [
    {
      title: t('feature.converter.title'),
      description: t('feature.converter.desc'),
      buttonText: t('feature.converter.btn'),
      href: '/dashboard/transcript-converter',
      comingSoon: false
    },
    {
      title: t('feature.analysis.title'),
      description: t('feature.analysis.desc'),
      buttonText: t('menu.analysis'),
      href: '/dashboard/analysis',
      comingSoon: true
    },
    {
      title: t('feature.insights.title'),
      description: t('feature.insights.desc'),
      buttonText: t('menu.insights'),
      href: '/dashboard/insights',
      comingSoon: true
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      {features.map((feature, index) => (
        <FeatureCard
          key={index}
          title={feature.title}
          description={feature.description}
          buttonText={feature.buttonText}
          href={feature.href}
          comingSoon={feature.comingSoon}
        />
      ))}
    </div>
  )
}
