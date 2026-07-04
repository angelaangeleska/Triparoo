import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Trans, useTranslation } from 'react-i18next'
import {
  ArrowRight,
  Baby,
  Calendar,
  Compass,
  Euro,
  MapPin,
  Sparkles,
  Users,
  Wallet,
} from 'lucide-react'
import FadeIn from '../components/ui/FadeIn'
import { Button } from '../components/ui/Button'
import { HERO_IMAGE } from '../utils/cityImages'

export default function HomePage() {
  const { t } = useTranslation()

  const features = [
    { icon: Sparkles, title: t('home.feature1Title'), description: t('home.feature1Desc'), color: 'from-brand-500 to-brand-600' },
    { icon: Euro, title: t('home.feature2Title'), description: t('home.feature2Desc'), color: 'from-sunset-500 to-sunset-600' },
    { icon: Calendar, title: t('home.feature3Title'), description: t('home.feature3Desc'), color: 'from-emerald-500 to-teal-600' },
    { icon: Baby, title: t('home.feature4Title'), description: t('home.feature4Desc'), color: 'from-violet-500 to-purple-600' },
  ]

  const steps = [
    { num: '01', title: t('home.step1Title'), desc: t('home.step1Desc') },
    { num: '02', title: t('home.step2Title'), desc: t('home.step2Desc') },
    { num: '03', title: t('home.step3Title'), desc: t('home.step3Desc') },
    { num: '04', title: t('home.step4Title'), desc: t('home.step4Desc') },
  ]

  const stats = [
    { label: t('home.statsDestinations'), value: '7+', icon: MapPin },
    { label: t('home.statsFactors'), value: '7', icon: Users },
    { label: t('home.statsAttractions'), value: '30+', icon: Sparkles },
    { label: t('home.statsTools'), value: '3', icon: Wallet },
  ]

  return (
    <>
      {/* Hero */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url('${HERO_IMAGE}')` }} />
        <div className="absolute inset-0 bg-hero-gradient" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(255,255,255,0.08),transparent_60%)]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 w-full">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="max-w-3xl"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur border border-white/20 text-white/90 text-sm font-medium mb-6">
              <Compass className="w-4 h-4" />
              {t('home.badge')}
            </div>
            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-white leading-[1.1] mb-6">
              {t('home.titleLine1')} <span className="text-sunset-400">{t('home.titleHighlight')}</span>
            </h1>
            <p className="text-lg sm:text-xl text-white/80 leading-relaxed mb-10 max-w-2xl">{t('home.subtitle')}</p>
            <div className="flex flex-wrap gap-4">
              <Button size="lg" asChild className="bg-white text-brand-800 hover:bg-sand-50 hover:from-white hover:to-white shadow-card">
                <Link to="/planner">
                  <Sparkles className="w-5 h-5" />
                  {t('home.ctaPlan')}
                  <ArrowRight className="w-5 h-5" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild className="border-white/30 text-white bg-white/10 hover:bg-white/20">
                <Link to="/destinations">
                  <MapPin className="w-5 h-5" />
                  {t('home.ctaBrowse')}
                </Link>
              </Button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl"
          >
            {stats.map(({ label, value, icon: Icon }) => (
              <div key={label} className="glass dark:bg-white/10 rounded-2xl p-4 text-center">
                <Icon className="w-5 h-5 text-brand-500 dark:text-brand-200 mx-auto mb-2" />
                <div className="text-2xl font-bold text-brand-900 dark:text-white">{value}</div>
                <div className="text-xs text-brand-600 dark:text-brand-200">{label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <FadeIn className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-brand-900 dark:text-white mb-4">
              {t('home.featuresTitle')}
            </h2>
            <p className="text-brand-600 dark:text-brand-300 text-lg max-w-2xl mx-auto">
              {t('home.featuresSubtitle')}
            </p>
          </FadeIn>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map(({ icon: Icon, title, description, color }, i) => (
              <FadeIn key={title} delay={i * 0.1}>
                <div className="glass dark:bg-brand-900/50 dark:border-brand-800 rounded-2xl p-6 h-full hover:shadow-card transition-shadow group">
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}
                  >
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-brand-900 dark:text-white text-lg mb-2">{title}</h3>
                  <p className="text-sm text-brand-600 dark:text-brand-300 leading-relaxed">{description}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-brand-900 dark:bg-brand-950">
        <div className="max-w-7xl mx-auto">
          <FadeIn className="text-center mb-16">
            <h2 className="font-display text-4xl font-bold text-white mb-4">{t('home.howItWorksTitle')}</h2>
            <p className="text-brand-300 text-lg">{t('home.howItWorksSubtitle')}</p>
          </FadeIn>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map(({ num, title, desc }, i) => (
              <FadeIn key={num} delay={i * 0.1}>
                <div className="relative">
                  <span className="font-display text-5xl font-bold text-brand-700/50">{num}</span>
                  <h3 className="text-white font-semibold text-lg mt-2 mb-2">{title}</h3>
                  <p className="text-brand-300 text-sm">{desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>

          <FadeIn delay={0.4} className="text-center mt-12">
            <Button size="lg" asChild className="hover:shadow-glow">
              <Link to="/register">
                {t('home.finalCta')}
                <ArrowRight className="w-5 h-5" />
              </Link>
            </Button>
          </FadeIn>
        </div>
      </section>

      {/* Example CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <div className="max-w-4xl mx-auto glass dark:bg-brand-900/50 dark:border-brand-800 rounded-3xl p-8 sm:p-12 text-center shadow-card relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-brand-400/20 to-transparent rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="relative">
              <p className="text-brand-500 dark:text-brand-300 font-semibold text-sm uppercase tracking-wider mb-3">
                {t('home.exampleLabel')}
              </p>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-brand-900 dark:text-white mb-4">
                {t('home.exampleTitle')}
              </h2>
              <p className="text-brand-600 dark:text-brand-300 text-lg mb-8 max-w-xl mx-auto">
                <Trans i18nKey="home.exampleDesc">
                  Our engine recommends <strong className="text-brand-800 dark:text-white">Paris & Disneyland Paris</strong> —
                  matching the child's age, summer season, and your family budget.
                </Trans>
              </p>
              <Button size="lg" asChild>
                <Link to="/planner">
                  {t('home.exampleCta')}
                  <ArrowRight className="w-5 h-5" />
                </Link>
              </Button>
            </div>
          </div>
        </FadeIn>
      </section>
    </>
  )
}
