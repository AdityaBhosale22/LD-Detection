import { useState } from 'react'
import { Link } from 'react-router'
import { AlertTriangle, CheckCircle2, ChevronRight, Circle, Download, ShieldCheck } from 'lucide-react'
import { Alert, Button, ButtonLink, Card, Meter, PageHeader, Spinner } from '../components/ui'
import { api, type Dashboard as DashboardData, type TestKind, type TestResult } from '../lib/api'
import { TESTS, TEST_BY_KIND, summarize } from '../lib/tests'
import { useLoad } from '../lib/useLoad'

const NEEDS_PRACTICE = 0.6

function ScreeningCard({ data, onChange }: { data: DashboardData; onChange: () => void }) {
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { intake, prediction } = data

  async function run() {
    setRunning(true)
    setError(null)
    try {
      await api.runPrediction()
      onChange()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setRunning(false)
    }
  }

  if (!intake) {
    return (
      <Card className="lg:col-span-2">
        <h2 className="text-lg font-semibold">Screening result</h2>
        <p className="mt-2 text-slate-600">Start with a short profile so the model has something to work with.</p>
        <ButtonLink to="/intake" className="mt-5">
          Fill in profile
        </ButtonLink>
      </Card>
    )
  }

  if (!prediction) {
    return (
      <Card className="lg:col-span-2">
        <h2 className="text-lg font-semibold">Screening result</h2>
        <p className="mt-2 text-slate-600">Your profile is saved. Run the screening model to see the result.</p>
        {error && <div className="mt-4"><Alert>{error}</Alert></div>}
        <Button onClick={run} loading={running} className="mt-5">
          Run screening
        </Button>
      </Card>
    )
  }

  const elevated = prediction.probability >= 0.5
  const Icon = elevated ? AlertTriangle : ShieldCheck
  return (
    <Card className="lg:col-span-2">
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-lg font-semibold">Screening result</h2>
        <span className="text-xs text-slate-500">{new Date(prediction.created_at).toLocaleDateString()}</span>
      </div>
      <div className="mt-4 flex items-center gap-3">
        <Icon className={elevated ? 'size-6 text-amber-600' : 'size-6 text-emerald-600'} aria-hidden />
        <p className="font-display text-xl font-semibold">
          {elevated ? 'Some indicators of a learning difficulty' : 'No strong indicators found'}
        </p>
      </div>
      <div className="mt-5">
        <div className="mb-1.5 flex justify-between text-sm">
          <span className="text-slate-600">Model probability</span>
          <span className="font-medium tabular-nums">{Math.round(prediction.probability * 100)}%</span>
        </div>
        <Meter value={prediction.probability} label="Model probability of learning difficulty indicators" />
      </div>
      <p className="mt-4 text-sm text-slate-500">
        A screening aid, not a diagnosis. {elevated && 'Consider discussing the report with a specialist.'}
      </p>
      <div className="mt-5 flex flex-wrap gap-2">
        <Button variant="secondary" onClick={run} loading={running}>
          Run again
        </Button>
        <ButtonLink to="/intake" variant="ghost">
          Update profile
        </ButtonLink>
      </div>
    </Card>
  )
}

function ProgressCard({ data }: { data: DashboardData }) {
  const done = Object.values(data.tests).filter(Boolean).length
  const steps = [
    { label: 'Profile', detail: data.intake ? 'Completed' : 'Not started', complete: !!data.intake, to: '/intake' },
    { label: 'Assessments', detail: `${done} of ${TESTS.length} completed`, complete: done === TESTS.length, to: '/tests' },
    { label: 'Screening', detail: data.prediction ? 'Completed' : 'Not run yet', complete: !!data.prediction, to: '/dashboard' },
  ]
  return (
    <Card>
      <h2 className="text-lg font-semibold">Progress</h2>
      <ol className="mt-4 space-y-1">
        {steps.map((step) => (
          <li key={step.label}>
            <Link to={step.to} className="flex items-center gap-3 rounded-lg p-2 -mx-2 hover:bg-slate-50">
              {step.complete ? (
                <CheckCircle2 className="size-5 text-brand-700" aria-label="Done" />
              ) : (
                <Circle className="size-5 text-slate-300" aria-label="To do" />
              )}
              <span className="flex-1">
                <span className="block text-sm font-medium">{step.label}</span>
                <span className="block text-sm text-slate-500">{step.detail}</span>
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </Card>
  )
}

function AreaChart({ areas }: { areas: DashboardData['areas'] }) {
  return (
    <Card>
      <h2 className="text-lg font-semibold">Performance by area</h2>
      <p className="mt-1 text-sm text-slate-500">Average across completed assessments.</p>
      {areas.length === 0 ? (
        <p className="mt-6 text-sm text-slate-600">Complete an assessment to see your results here.</p>
      ) : (
        <ul className="mt-5 space-y-4">
          {areas.map(({ area, score }) => {
            const performance = 1 - score
            return (
              <li key={area} title={`${TEST_BY_KIND[area].area}: ${Math.round(performance * 100)}%`}>
                <div className="mb-1.5 flex items-center justify-between gap-2 text-sm">
                  <span className="font-medium">{TEST_BY_KIND[area].area}</span>
                  <span className="flex items-center gap-2">
                    {performance < NEEDS_PRACTICE && (
                      <span className="flex items-center gap-1 text-xs text-amber-700">
                        <AlertTriangle className="size-3.5" aria-hidden /> Needs practice
                      </span>
                    )}
                    <span className="tabular-nums text-slate-700">{Math.round(performance * 100)}%</span>
                  </span>
                </div>
                <Meter value={performance} label={`${TEST_BY_KIND[area].area} performance`} />
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}

function TestsCard({ tests }: { tests: Record<TestKind, TestResult | null> }) {
  return (
    <Card flush>
      <h2 className="px-5 pt-5 text-lg font-semibold sm:px-6 sm:pt-6">Assessments</h2>
      <ul className="mt-3 divide-y divide-slate-100">
        {TESTS.map((test) => {
          const result = tests[test.kind]
          return (
            <li key={test.kind}>
              <Link
                to={result ? `/tests/${test.kind}/${result.id}/result` : `/tests/${test.kind}`}
                className="flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50 sm:px-6"
              >
                <test.icon className="size-5 text-slate-500" aria-hidden />
                <span className="flex-1 text-sm font-medium">{test.name}</span>
                <span className={result ? 'text-sm text-slate-700' : 'text-sm text-slate-400'}>
                  {result ? summarize(result) : 'Not taken'}
                </span>
                <ChevronRight className="size-4 text-slate-400" aria-hidden />
              </Link>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}

export default function Dashboard() {
  const { data, error, loading, reload } = useLoad(api.dashboard)
  const [downloading, setDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  async function download() {
    setDownloading(true)
    setDownloadError(null)
    try {
      await api.downloadReport()
    } catch (err) {
      setDownloadError((err as Error).message)
    } finally {
      setDownloading(false)
    }
  }

  if (loading && !data) return <Spinner label="Loading dashboard" />
  if (error || !data) return <Alert>{error ?? 'Could not load the dashboard.'}</Alert>

  return (
    <>
      <PageHeader
        title={`Hi ${data.user.first_name || 'there'}`}
        description="Your screening progress at a glance."
        action={
          <Button variant="secondary" onClick={download} loading={downloading}>
            {!downloading && <Download className="size-4" aria-hidden />} Download report
          </Button>
        }
      />
      {downloadError && <div className="mb-6"><Alert>{downloadError}</Alert></div>}
      <div className="grid gap-6 lg:grid-cols-3">
        <ScreeningCard data={data} onChange={reload} />
        <ProgressCard data={data} />
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <TestsCard tests={data.tests} />
        <AreaChart areas={data.areas} />
      </div>
    </>
  )
}
