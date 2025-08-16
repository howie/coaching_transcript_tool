// Main translations index - combines all modular translations
import { navTranslations } from './translations/nav'
import { dashboardTranslations } from './translations/dashboard'
import { menuTranslations } from './translations/menu'
import { commonTranslations } from './translations/common'
import { audioTranslations } from './translations/audio'
import { accountTranslations } from './translations/account'
import { sessionsTranslations } from './translations/sessions'
import { clientsTranslations } from './translations/clients'
import { billingTranslations } from './translations/billing'
import { profileTranslations } from './translations/profile'
import { helpTranslations } from './translations/help'
import { layoutTranslations } from './translations/layout'
import { converterTranslations } from './translations/converter'
import { authTranslations } from './translations/auth'
import { landingTranslations } from './translations/landing'

// Combine all translations
export const translations = {
  zh: {
    ...navTranslations.zh,
    ...dashboardTranslations.zh,
    ...menuTranslations.zh,
    ...commonTranslations.zh,
    ...audioTranslations.zh,
    ...accountTranslations.zh,
    ...sessionsTranslations.zh,
    ...clientsTranslations.zh,
    ...billingTranslations.zh,
    ...profileTranslations.zh,
    ...helpTranslations.zh,
    ...layoutTranslations.zh,
    ...converterTranslations.zh,
    ...authTranslations.zh,
    ...landingTranslations.zh,
  },
  en: {
    ...navTranslations.en,
    ...dashboardTranslations.en,
    ...menuTranslations.en,
    ...commonTranslations.en,
    ...audioTranslations.en,
    ...accountTranslations.en,
    ...sessionsTranslations.en,
    ...clientsTranslations.en,
    ...billingTranslations.en,
    ...profileTranslations.en,
    ...helpTranslations.en,
    ...layoutTranslations.en,
    ...converterTranslations.en,
    ...authTranslations.en,
    ...landingTranslations.en,
  }
}

export type Language = 'zh' | 'en'
export type TranslationKey = keyof typeof translations['zh']

// Re-export for backward compatibility
export default translations