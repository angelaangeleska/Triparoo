import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import en from './locales/en.json'
import mk from './locales/mk.json'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      mk: { translation: mk },
    },
    fallbackLng: 'en',
    supportedLngs: ['en', 'mk'],
    interpolation: { escapeValue: false },
    detection: {
      // Only ever restore an explicit user choice — never auto-switch based on
      // browser/OS locale, since the product default is English regardless of visitor origin.
      order: ['localStorage'],
      lookupLocalStorage: 'language',
      caches: ['localStorage'],
    },
  })

export default i18n
