import { useEffect } from 'react'
import { ArrowRight, ClipboardList, FileText, LineChart } from 'lucide-react'
import { ButtonLink } from '../components/ui'
import { Logo, REPO_URL } from '../components/Layout'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'
import { TESTS } from '../lib/tests'

const STEPS = [
  { icon: ClipboardList, title: 'Share a short profile', text: 'Age, attention span and any reading concerns. Takes a minute.' },
  { icon: LineChart, title: 'Take five quick tests', text: 'Math, grammar, reading aloud, memory and comprehension.' },
  { icon: FileText, title: 'Get a clear report', text: 'A screening result, weak areas and practice suggestions as a PDF.' },
]

export default function Landing() {
  const { user } = useAuth()

  useEffect(() => {
    api.wake()
  }, [])

  return (
    <div className="min-h-dvh bg-white">
      <header className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
        <Logo />
        <nav className="flex items-center gap-2">
          {user ? (
            <ButtonLink to="/dashboard">Open dashboard</ButtonLink>
          ) : (
            <>
              <ButtonLink to="/login" variant="ghost">Sign in</ButtonLink>
              <ButtonLink to="/register">Get started</ButtonLink>
            </>
          )}
        </nav>
      </header>

      <main>
        <section className="mx-auto max-w-3xl px-4 pt-16 pb-20 text-center sm:pt-24">
          <p className="mb-4 text-sm font-medium text-brand-700">Learning difficulty screening</p>
          <h1 className="text-4xl font-semibold text-balance sm:text-5xl">
            Spot early signs of learning difficulties in under 15 minutes
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-lg text-pretty text-slate-600">
            Short, friendly assessments for students, with a machine-learning screening result and practical next steps
            for parents and teachers.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <ButtonLink to={user ? '/dashboard' : '/register'} className="px-6">
              {user ? 'Continue' : 'Start screening'} <ArrowRight className="size-4" aria-hidden />
            </ButtonLink>
            <ButtonLink to="/login" variant="secondary" className="px-6">
              I have an account
            </ButtonLink>
          </div>
        </section>

        <section className="border-y border-slate-200 bg-slate-50 py-16">
          <div className="mx-auto max-w-5xl px-4">
            <h2 className="text-center text-2xl font-semibold">How it works</h2>
            <ol className="mt-10 grid gap-6 sm:grid-cols-3">
              {STEPS.map((step, i) => (
                <li key={step.title} className="rounded-xl border border-slate-200 bg-white p-6">
                  <div className="flex items-center gap-3">
                    <span className="flex size-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                      <step.icon className="size-5" aria-hidden />
                    </span>
                    <span className="text-sm text-slate-500">Step {i + 1}</span>
                  </div>
                  <h3 className="mt-4 font-semibold">{step.title}</h3>
                  <p className="mt-1.5 text-sm text-slate-600">{step.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-4 py-16">
          <h2 className="text-center text-2xl font-semibold">Five areas, one picture</h2>
          <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {TESTS.map((test) => (
              <li key={test.kind} className="rounded-xl border border-slate-200 p-5">
                <test.icon className="size-5 text-brand-700" aria-hidden />
                <h3 className="mt-3 font-semibold">{test.name}</h3>
                <p className="mt-1 text-sm text-slate-600">{test.description}</p>
              </li>
            ))}
          </ul>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-8">
        <div className="mx-auto flex max-w-5xl flex-col gap-2 px-4 text-sm text-slate-500 sm:flex-row sm:justify-between">
          <p>A screening aid, not a medical diagnosis. Consult a qualified professional for an assessment.</p>
          <a href={REPO_URL} className="underline-offset-4 hover:text-slate-900 hover:underline" target="_blank" rel="noreferrer">
            Source on GitHub
          </a>
        </div>
      </footer>
    </div>
  )
}
