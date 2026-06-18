import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
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
import { HERO_IMAGE } from '../utils/cityImages'

const features = [
  {
    icon: Sparkles,
    title: 'Smart Recommendations',
    description: 'Hybrid AI engine scores destinations by child age, budget, season, and family interests.',
    color: 'from-brand-500 to-brand-600',
  },
  {
    icon: Euro,
    title: 'Budget Optimizer',
    description: 'Find cheaper dates, accommodations, and alternative destinations that fit your wallet.',
    color: 'from-sunset-500 to-sunset-600',
  },
  {
    icon: Calendar,
    title: 'Day-by-Day Itineraries',
    description: 'Auto-generated travel plans with age-appropriate activities for every family member.',
    color: 'from-emerald-500 to-teal-600',
  },
  {
    icon: Baby,
    title: 'Child-Friendly Activities',
    description: 'Discover Disneyland, museums, parks and more matched to your child\'s age and interests.',
    color: 'from-violet-500 to-purple-600',
  },
]

const steps = [
  { num: '01', title: 'Tell us about your family', desc: 'Ages, interests, and travel preferences' },
  { num: '02', title: 'Set your budget & dates', desc: 'We find the best fit for your schedule' },
  { num: '03', title: 'Get personalized picks', desc: 'Ranked destinations with clear explanations' },
  { num: '04', title: 'Plan your adventure', desc: 'Itineraries, activities, and budget tips' },
]

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{
            backgroundImage: `url('${HERO_IMAGE}')`,
          }}
        />
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
              Intelligent family travel planning
            </div>
            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-white leading-[1.1] mb-6">
              Adventures made for{' '}
              <span className="text-sunset-400">every generation</span>
            </h1>
            <p className="text-lg sm:text-xl text-white/80 leading-relaxed mb-10 max-w-2xl">
              Discover the perfect destination for your family. From Disneyland Paris for the kids to
              cultural gems for everyone — planned around your budget and dates.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                to="/planner"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white text-brand-800 font-semibold rounded-2xl hover:bg-sand-50 shadow-card transition-all hover:scale-[1.02]"
              >
                <Sparkles className="w-5 h-5" />
                Plan your trip
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                to="/destinations"
                className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 backdrop-blur border border-white/30 text-white font-semibold rounded-2xl hover:bg-white/20 transition-all"
              >
                <MapPin className="w-5 h-5" />
                Browse destinations
              </Link>
            </div>
          </motion.div>

          {/* Floating stats */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl"
          >
            {[
              { label: 'Destinations', value: '7+', icon: MapPin },
              { label: 'Family Score Factors', value: '7', icon: Users },
              { label: 'Attractions', value: '30+', icon: Sparkles },
              { label: 'Budget Tools', value: '3', icon: Wallet },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="glass rounded-2xl p-4 text-center">
                <Icon className="w-5 h-5 text-brand-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-brand-900">{value}</div>
                <div className="text-xs text-brand-600">{label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <FadeIn className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-brand-900 mb-4">
              Everything your family needs
            </h2>
            <p className="text-brand-600 text-lg max-w-2xl mx-auto">
              More than a search engine — a complete travel intelligence platform built for families.
            </p>
          </FadeIn>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map(({ icon: Icon, title, description, color }, i) => (
              <FadeIn key={title} delay={i * 0.1}>
                <div className="glass rounded-2xl p-6 h-full hover:shadow-card transition-shadow group">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-brand-900 text-lg mb-2">{title}</h3>
                  <p className="text-sm text-brand-600 leading-relaxed">{description}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-brand-900">
        <div className="max-w-7xl mx-auto">
          <FadeIn className="text-center mb-16">
            <h2 className="font-display text-4xl font-bold text-white mb-4">How it works</h2>
            <p className="text-brand-300 text-lg">Four simple steps to your perfect family trip</p>
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
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-brand-500 to-brand-400 text-white font-semibold rounded-2xl hover:shadow-glow transition-all"
            >
              Start planning for free
              <ArrowRight className="w-5 h-5" />
            </Link>
          </FadeIn>
        </div>
      </section>

      {/* Example CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <FadeIn>
          <div className="max-w-4xl mx-auto glass rounded-3xl p-8 sm:p-12 text-center shadow-card relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-brand-400/20 to-transparent rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="relative">
              <p className="text-brand-500 font-semibold text-sm uppercase tracking-wider mb-3">Example</p>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-brand-900 mb-4">
                2 adults · 1 girl (11) · €1,500 · August
              </h2>
              <p className="text-brand-600 text-lg mb-8 max-w-xl mx-auto">
                Our engine recommends <strong className="text-brand-800">Paris & Disneyland Paris</strong> — matching
                the child's age, summer season, and your family budget.
              </p>
              <Link
                to="/planner"
                className="inline-flex items-center gap-2 px-8 py-4 bg-brand-600 text-white font-semibold rounded-2xl hover:bg-brand-700 transition-colors"
              >
                Try it yourself
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
        </FadeIn>
      </section>
    </>
  )
}
