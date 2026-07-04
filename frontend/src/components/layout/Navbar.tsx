import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Compass, History, LogOut, MapPin, Menu, Sparkles, User, Users } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../ui/Button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/DropdownMenu'
import { Sheet, SheetContent, SheetTrigger } from '../ui/Sheet'
import ThemeToggle from './ThemeToggle'
import LanguageToggle from './LanguageToggle'

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const navLinks = [
    { to: '/destinations', label: t('nav.destinations'), icon: MapPin },
    { to: '/planner', label: t('nav.planner'), icon: Sparkles },
    ...(isAuthenticated
      ? [
          { to: '/family', label: t('nav.family'), icon: Users },
          { to: '/trips', label: t('nav.trips'), icon: History },
        ]
      : []),
  ]

  const handleLogout = () => {
    logout()
    navigate('/')
    setMobileOpen(false)
  }

  return (
    <header className="fixed top-0 inset-x-0 z-50 glass dark:bg-brand-950/70 dark:border-brand-800/50 shadow-soft">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-glow group-hover:scale-105 transition-transform">
              <Compass className="w-5 h-5 text-white" />
            </div>
            <span className="font-display text-xl font-semibold text-brand-900 dark:text-white hidden sm:block">
              Triparoo
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-brand-500/10 text-brand-700 dark:bg-brand-400/10 dark:text-brand-200'
                      : 'text-brand-600 hover:bg-brand-50 hover:text-brand-800 dark:text-brand-300 dark:hover:bg-brand-800/60 dark:hover:text-white'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                {label}
              </NavLink>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-2">
            <ThemeToggle />
            <LanguageToggle />
            {isAuthenticated ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="gap-2 rounded-full pl-2 pr-3">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-500 text-white text-xs font-bold">
                      {(user?.first_name || user?.username || '?').charAt(0).toUpperCase()}
                    </span>
                    <span className="max-w-[8rem] truncate">{user?.first_name || user?.username}</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => navigate('/family')}>
                    <Users className="w-4 h-4" /> {t('nav.family')}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-sunset-600 dark:text-sunset-400">
                    <LogOut className="w-4 h-4" /> {t('nav.signOut')}
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/login">{t('nav.signIn')}</Link>
                </Button>
                <Button size="sm" asChild>
                  <Link to="/register">{t('nav.getStarted')}</Link>
                </Button>
              </>
            )}
          </div>

          <div className="md:hidden flex items-center gap-1">
            <ThemeToggle />
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Open menu">
                  <Menu className="w-6 h-6" />
                </Button>
              </SheetTrigger>
              <SheetContent>
                <div className="flex flex-col gap-1 mt-8">
                  {navLinks.map(({ to, label, icon: Icon }) => (
                    <NavLink
                      key={to}
                      to={to}
                      onClick={() => setMobileOpen(false)}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl text-brand-700 hover:bg-brand-50 dark:text-brand-100 dark:hover:bg-brand-800"
                    >
                      <Icon className="w-5 h-5" />
                      {label}
                    </NavLink>
                  ))}
                  <div className="px-4 py-3">
                    <LanguageToggle />
                  </div>
                  {isAuthenticated ? (
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl text-sunset-600 hover:bg-sunset-400/10 text-left"
                    >
                      <LogOut className="w-5 h-5" />
                      {t('nav.signOut')}
                    </button>
                  ) : (
                    <>
                      <Link
                        to="/login"
                        onClick={() => setMobileOpen(false)}
                        className="flex items-center gap-3 px-4 py-3 text-brand-700 dark:text-brand-100"
                      >
                        <User className="w-5 h-5" />
                        {t('nav.signIn')}
                      </Link>
                      <Link
                        to="/register"
                        onClick={() => setMobileOpen(false)}
                        className="block mx-4 py-3 text-center text-white bg-brand-500 rounded-xl font-semibold"
                      >
                        {t('nav.getStarted')}
                      </Link>
                    </>
                  )}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </nav>
    </header>
  )
}
