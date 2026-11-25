import { ExternalLink } from 'lucide-react'
import { Alert, ButtonLink, Card, Meter, PageHeader, Spinner } from '../components/ui'
import { api } from '../lib/api'
import { TEST_BY_KIND } from '../lib/tests'
import { useLoad } from '../lib/useLoad'

export default function Recommendations() {
  const { data, error, loading } = useLoad(api.recommendations)

  if (loading) return <Spinner />
  if (error || !data) return <Alert>{error ?? 'Could not load recommendations.'}</Alert>

  return (
    <>
      <PageHeader
        title="Recommendations"
        description="Practice suggestions for the areas that need the most attention, weakest first."
      />
      {data.length === 0 ? (
        <Card className="text-center">
          <p className="text-slate-600">
            No suggestions yet. Complete a few assessments, or keep it up if every area is going well.
          </p>
          <ButtonLink to="/tests" className="mt-5">
            Go to assessments
          </ButtonLink>
        </Card>
      ) : (
        <ul className="space-y-4">
          {data.map((rec) => {
            const Icon = TEST_BY_KIND[rec.area].icon
            return (
              <li key={rec.area}>
                <Card>
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
                    <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                      <Icon className="size-5" aria-hidden />
                    </span>
                    <div className="flex-1">
                      <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">{rec.area_label}</p>
                      <h2 className="mt-1 text-lg font-semibold">{rec.title}</h2>
                      <p className="mt-1 text-slate-600">{rec.description}</p>
                      {rec.url && (
                        <a
                          href={rec.url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-3 inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-brand-700 hover:underline"
                        >
                          Open practice resource <ExternalLink className="size-4" aria-hidden />
                        </a>
                      )}
                    </div>
                    <div className="sm:w-40">
                      <div className="mb-1.5 flex justify-between text-sm">
                        <span className="text-slate-600">Priority</span>
                        <span className="font-medium tabular-nums">{Math.round(rec.score * 100)}%</span>
                      </div>
                      <Meter value={rec.score} label={`${rec.area_label} priority`} />
                    </div>
                  </div>
                </Card>
              </li>
            )
          })}
        </ul>
      )}
    </>
  )
}
