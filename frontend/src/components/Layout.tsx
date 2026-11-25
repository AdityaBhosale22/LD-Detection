import { useState } from 'react'
import { cx } from '../lib/cx'
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router'
import { LogOut, Menu, X } from 'lucide-react'
import { useAuth } from '../lib/auth'
import { Spinner } from './ui'

export const REPO_URL = 'https://github.com/AdityaBhosale22/LD-Detection'

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2 font-display text-lg font-semibold text-slate-900">
      <img src="/favicon.svg" alt="" className="size-7" />
      LD Detect
    </Link>
  )
}

const NAV = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/intake', label: 'Profile' },
  { to: '/tests', label: 'Assessments' },
  { to: '/recommendations', label: 'Recommendations' },
]

function navClass({ isActive }: { isActive: boolean }) {
  return cx(
    'rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:text-slate-900',
  )
}

/** Shell for signed-in pages; sends anonymous visitors to /login. */
export function AppLayout() {
  const { user, loading, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const location = useLocation()

  if (loading) return <Spinner />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
          <Logo />
          <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-1">
            <span className="hidden text-sm text-slate-500 lg:inline">{user.email}</span>
            <button
              onClick={logout}
              className="hidden min-h-11 cursor-pointer items-center gap-1.5 rounded-lg px-3 text-sm text-slate-600 hover:bg-slate-100 hover:text-slate-900 md:inline-flex"
            >
              <LogOut className="size-4" aria-hidden /> Sign out
            </button>
            <button
              className="inline-flex size-11 cursor-pointer items-center justify-center rounded-lg text-slate-700 hover:bg-slate-100 md:hidden"
              aria-label={open ? 'Close menu' : 'Open menu'}
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
            >
              {open ? <X className="size-5" /> : <Menu className="size-5" />}
            </button>
          </div>
        </div>
        {open && (
          <nav aria-label="Mobile" className="border-t border-slate-200 px-4 py-2 md:hidden">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} className={(s) => cx(navClass(s), 'block')} onClick={() => setOpen(false)}>
                {item.label}
              </NavLink>
            ))}
            <button onClick={logout} className="block w-full cursor-pointer rounded-lg px-3 py-2 text-left text-sm font-medium text-slate-600">
              Sign out
            </button>
          </nav>
        )}
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8 sm:py-12">
        <Outlet />
      </main>
    </div>
  )
}
