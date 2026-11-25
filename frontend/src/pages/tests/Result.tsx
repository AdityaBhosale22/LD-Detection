import { Link, Navigate, useParams } from 'react-router'
import { ArrowLeft, CheckCircle2, XCircle } from 'lucide-react'
import { useCallback } from 'react'
import { Alert, ButtonLink, Card, Spinner } from '../../components/ui'
import { api, type TestKind, type TestResult } from '../../lib/api'
import { TEST_BY_KIND, formatDuration, isTestKind } from '../../lib/tests'
import { useLoad } from '../../lib/useLoad'

type Row = { question: string; given: string; expected: string; correct: boolean }

function rowsFor(kind: TestKind, result: TestResult): Row[] {
  const details = (result.details ?? []) as Record<string, unknown>[]
  const str = (v: unknown) => (v === null || v === undefined || v === '' ? '—' : String(v))
  return details.map((d) => {
    switch (kind) {
      case 'math':
        return { question: `${d.a} ${d.op === '-' ? '−' : '+'} ${d.b}`, given: str(d.user), expected: str(d.answer), correct: !!d.correct }
      case 'memory':
        return { question: 'Digit', given: str(d.user), expected: str(d.target), correct: !!d.correct }
      case 'scenario':
        return { question: str(d.q), given: str(d.user), expected: str(d.a), correct: !!d.correct }
      default:
        return { question: str(d.prompt), given: str(d.user), expected: str(d.answer), correct: !!d.correct }
    }
  })
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className="mt-1 font-display text-3xl font-semibold tabular-nums">{value}</p>
    </div>
  )
}

export default function Result() {
  const { kind, id } = useParams()
  const valid = isTestKind(kind) && !!id
  const loader = useCallback(() => api.getResult(kind as TestKind, Number(id)), [kind, id])
  const { data, error, loading } = useLoad(loader)

  if (!valid) return <Navigate to="/tests" replace />
  if (loading) return <Spinner />
  if (error || !data) return <Alert>{error ?? 'Result not found.'}</Alert>

  const info = TEST_BY_KIND[kind]
  const isReading = kind === 'reading'
  const rows = isReading ? [] : rowsFor(kind, data)

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/tests" className="mb-6 inline-flex min-h-11 items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900">
        <ArrowLeft className="size-4" aria-hidden /> All assessments
      </Link>
      <h1 className="text-2xl font-semibold">{info.name} result</h1>

      {!data.completed ? (
        <Card className="mt-6">
          <p className="text-slate-600">This test was started but not submitted.</p>
          <ButtonLink to={`/tests/${kind}`} className="mt-4">Start again</ButtonLink>
        </Card>
      ) : (
        <>
          <Card className="mt-6">
            <div className="grid grid-cols-2 gap-6">
              {isReading ? (
                <>
                  <Stat label="Reading speed" value={`${Math.round(data.wpm ?? 0)} wpm`} />
                  <Stat label="Word accuracy" value={`${Math.round((data.accuracy ?? 0) * 100)}%`} />
                </>
              ) : (
                <>
                  <Stat label="Score" value={`${data.num_correct} / ${data.num_total}`} />
                  <Stat label="Time taken" value={formatDuration(data.duration_seconds)} />
                </>
              )}
            </div>
          </Card>

          {isReading ? (
            <Card className="mt-4">
              <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Passage</p>
              <p className="mt-1.5">{data.passage}</p>
              <p className="mt-4 text-xs font-medium tracking-wide text-slate-500 uppercase">What we heard</p>
              <p className="mt-1.5 text-slate-700">{data.transcript}</p>
              <p className="mt-4 text-sm text-slate-500">Typical reading speed for this age is 80–150 words per minute.</p>
            </Card>
          ) : (
            <Card flush className="mt-4">
              <h2 className="px-5 pt-5 font-semibold sm:px-6 sm:pt-6">Answers</h2>
              <ul className="mt-3 divide-y divide-slate-100">
                {rows.map((row, i) => (
                  <li key={i} className="flex items-start gap-3 px-5 py-3 sm:px-6">
                    {row.correct ? (
                      <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" aria-label="Correct" />
                    ) : (
                      <XCircle className="mt-0.5 size-5 shrink-0 text-red-600" aria-label="Incorrect" />
                    )}
                    <div className="flex-1 text-sm">
                      <p className="font-medium">{kind === 'memory' ? `Position ${i + 1}` : row.question}</p>
                      <p className="text-slate-600">
                        Your answer: {row.given}
                        {!row.correct && <span className="text-slate-500"> · Correct: {row.expected}</span>}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}

      <div className="mt-6 flex flex-wrap gap-2">
        <ButtonLink to="/dashboard">Back to dashboard</ButtonLink>
        <ButtonLink to={`/tests/${kind}`} variant="secondary">
          Retake
        </ButtonLink>
      </div>
    </div>
  )
}
