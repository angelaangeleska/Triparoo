import { Compass, Github, Heart } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export default function Footer() {
  const { t } = useTranslation()

  return (
    <footer className="bg-brand-900 dark:bg-brand-950 text-brand-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
                <Compass className="w-4 h-4 text-white" />
              </div>
              <span className="font-display text-lg text-white">Triparoo</span>
            </div>
            <p className="text-sm text-brand-300 leading-relaxed">{t('footer.tagline')}</p>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">{t('footer.explore')}</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/destinations" className="hover:text-white transition-colors">
                  {t('nav.destinations')}
                </Link>
              </li>
              <li>
                <Link to="/planner" className="hover:text-white transition-colors">
                  {t('nav.planner')}
                </Link>
              </li>
              <li>
                <Link to="/login" className="hover:text-white transition-colors">
                  {t('nav.signIn')}
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold mb-4">{t('footer.builtWith')}</h4>
            <p className="text-sm text-brand-300">{t('footer.stack')}</p>
            <p className="text-sm text-brand-400 mt-4 flex items-center gap-1">
              {t('footer.madeFor')} <Heart className="w-3.5 h-3.5 text-sunset-500 fill-sunset-500" />
            </p>
          </div>
        </div>

        <div className="border-t border-brand-800 mt-10 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-brand-400">
          <span>
            © {new Date().getFullYear()} Triparoo — {t('footer.rights')}
          </span>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 hover:text-white transition-colors"
          >
            <Github className="w-4 h-4" />
            {t('footer.apiDocs')}
          </a>
        </div>
      </div>
    </footer>
  )
}
