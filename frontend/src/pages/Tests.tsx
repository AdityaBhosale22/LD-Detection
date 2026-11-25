import { Link } from 'react-router'
import { CheckCircle2, Clock } from 'lucide-react'
import { Alert, PageHeader, Spinner } from '../components/ui'
import { api } from '../lib/api'
import { TESTS, summarize } from '../lib/tests'
import { useLoad } from '../lib/useLoad'

export default function Tests() {
  const { data, error, loading } = useLoad(api.dashboard)

  if (loading) return <Spinner />
  if (error || !data) return <Alert>{error ?? 'Could not load assessments.'}</Alert>

  return (
    <>
      <PageHeader title="Assessments" description="Five short tests. Take them in any order; you can retake them at any time." />
      <ul className="grid gap-4 sm:grid-cols-2">
        {TESTS.map((test) => {
          const result = data.tests[test.kind]
          return (
            <li key={test.kind}>
              <Link
                to={`/tests/${test.kind}`}
                className="group flex h-full flex-col rounded-xl border border-slate-200 bg-white p-5 transition-colors hover:border-brand-600"
              >
                <div className="flex items-center justify-between">
                  <span className="flex size-10 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                    <test.icon className="size-5" aria-hidden />
                  </span>
                  {result ? (
                    <span className="flex items-center gap-1 text-xs font-medium text-brand-700">
                      <CheckCircle2 className="size-4" aria-hidden /> Completed
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      <Clock className="size-4" aria-hidden /> ~{test.minutes} min
                    </span>
                  )}
                </div>
                <h2 className="mt-4 text-lg font-semibold">{test.name}</h2>
                <p className="mt-1 flex-1 text-sm text-slate-600">{test.description}</p>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className="text-slate-500">{result ? `Last: ${summarize(result)}` : 'Not taken yet'}</span>
                  <span className="font-medium text-brand-700 group-hover:underline">{result ? 'Retake' : 'Start'}</span>
                </div>
              </Link>
            </li>
          )
        })}
      </ul>
    </>
  )
}
