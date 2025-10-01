'use client'

import Link from 'next/link'
import { useI18n } from '@/contexts/i18n-context'
import { trackDashboard } from '@/lib/analytics'

interface StepProps {
  number: string
  title: string
  description: string
  href?: string
}

function Step({ number, title, description, href }: StepProps) {
  const handleClick = () => {
    if (href) {
      trackDashboard.quickStartStepClick(parseInt(number))
    }
  }

  const content = (
    <div className="flex items-start space-x-4">
      <div className="flex-shrink-0">
        <div className="w-8 h-8 bg-dashboard-accent text-white rounded-full flex items-center justify-center text-sm font-bold">
          {number}
        </div>
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-semibold text-foreground mb-2">
          {title}
        </h3>
        <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
          {description}
        </p>
      </div>
    </div>
  )

  const className = `bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-sm ${
    href ? 'hover:shadow-md transition-shadow cursor-pointer hover:border-dashboard-accent' : ''
  }`

  if (href) {
    return (
      <Link href={href as any} className={className} onClick={handleClick}>
        {content}
      </Link>
    )
  }

  return (
    <div className={className}>
      {content}
    </div>
  )
}

export function GettingStarted() {
  const { t } = useI18n()

  const steps = [
    {
      number: '1',
      title: t('dashboard.step1.title'),
      description: t('dashboard.step1.desc'),
      href: '/dashboard/clients/new'
    },
    {
      number: '2',
      title: t('dashboard.step2.title'),
      description: t('dashboard.step2.desc'),
      href: '/dashboard/sessions'
    },
    {
      number: '3',
      title: t('dashboard.step3.title'),
      description: t('dashboard.step3.desc'),
      href: '/dashboard/transcript-converter'
    },
    {
      number: '4',
      title: t('dashboard.step4.title'),
      description: t('dashboard.step4.desc'),
      href: '/dashboard/sessions'
    }
  ]

  return (
    <div className="mb-8">
      <h2 className="text-xl font-bold text-foreground mb-6">
        {t('dashboard.getting_started')}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {steps.map((step, index) => (
          <Step
            key={index}
            number={step.number}
            title={step.title}
            description={step.description}
            href={step.href}
          />
        ))}
      </div>
    </div>
  )
}
