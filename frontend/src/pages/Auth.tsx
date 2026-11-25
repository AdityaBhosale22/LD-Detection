import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router'
import { Alert, Button, Input, Select } from '../components/ui'
import { Logo } from '../components/Layout'
import { ApiError, api, type Role } from '../lib/api'
import { useAuth } from '../lib/auth'

function AuthShell({ title, subtitle, children }: { title: string; subtitle: ReactNode; children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-4 py-12">
      <div className="mb-8">
        <Logo />
      </div>
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 sm:p-8">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="mt-1.5 text-sm text-slate-600">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </div>
    </div>
  )
}

/** Free hosting can take ~a minute to wake; tell the user instead of looking stuck. */
function useSlowNotice(active: boolean) {
  const [slow, setSlow] = useState(false)
  const timer = useRef<number | undefined>(undefined)
  useEffect(() => {
    if (active) timer.current = window.setTimeout(() => setSlow(true), 4000)
    return () => {
      window.clearTimeout(timer.current)
      setSlow(false)
    }
  }, [active])
  return slow
}

function useAuthForm() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fields, setFields] = useState<Record<string, string>>({})
  const slow = useSlowNotice(busy)

  async function run(action: () => Promise<void>) {
    setBusy(true)
    setError(null)
    setFields({})
    try {
      await action()
    } catch (err) {
      const fieldErrors = err instanceof ApiError ? err.fields : {}
      const shownInline = Object.keys(fieldErrors).some((key) => key !== 'non_field_errors')
      setFields(fieldErrors)
      // Field errors appear under their inputs; anything else goes in the banner.
      setError(shownInline ? null : (err as Error).message)
      setBusy(false)
    }
  }
  return { busy, error, fields, slow, run }
}

export function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const from = (useLocation().state as { from?: string } | null)?.from ?? '/dashboard'
  const { busy, error, fields, slow, run } = useAuthForm()

  useEffect(() => {
    api.wake()
  }, [])

  if (user) return <Navigate to={from} replace />

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    run(async () => {
      await login(String(form.get('email')), String(form.get('password')))
      navigate(from, { replace: true })
    })
  }

  return (
    <AuthShell
      title="Sign in"
      subtitle={
        <>
          New here?{' '}
          <Link to="/register" className="font-medium text-brand-700 hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {error && <Alert>{error}</Alert>}
        <Input label="Email" name="email" type="email" autoComplete="email" required error={fields.email} />
        <Input label="Password" name="password" type="password" autoComplete="current-password" required error={fields.password} />
        <Button type="submit" loading={busy} className="w-full">
          Sign in
        </Button>
        {slow && <Alert tone="info">The server is waking up after being idle. This can take up to a minute.</Alert>}
      </form>
    </AuthShell>
  )
}

export function Register() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const { busy, error, fields, slow, run } = useAuthForm()

  useEffect(() => {
    api.wake()
  }, [])

  if (user) return <Navigate to="/dashboard" replace />

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    run(async () => {
      await register({
        email: String(form.get('email')),
        password: String(form.get('password')),
        first_name: String(form.get('first_name')),
        last_name: String(form.get('last_name')),
        role: String(form.get('role')) as Role,
      })
      navigate('/intake', { replace: true })
    })
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle={
        <>
          Already registered?{' '}
          <Link to="/login" className="font-medium text-brand-700 hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        {error && <Alert>{error}</Alert>}
        <div className="grid grid-cols-2 gap-3">
          <Input label="First name" name="first_name" autoComplete="given-name" error={fields.first_name} />
          <Input label="Last name" name="last_name" autoComplete="family-name" error={fields.last_name} />
        </div>
        <Input label="Email" name="email" type="email" autoComplete="email" required error={fields.email} />
        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          hint="At least 8 characters, not too common."
          error={fields.password}
        />
        <Select label="I am a" name="role" defaultValue="student" error={fields.role}>
          <option value="student">Student</option>
          <option value="parent">Parent</option>
          <option value="teacher">Teacher</option>
        </Select>
        <Button type="submit" loading={busy} className="w-full">
          Create account
        </Button>
        {slow && <Alert tone="info">The server is waking up after being idle. This can take up to a minute.</Alert>}
      </form>
    </AuthShell>
  )
}
