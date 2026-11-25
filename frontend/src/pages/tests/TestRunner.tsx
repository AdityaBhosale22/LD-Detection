import { useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router'
import { ArrowLeft, Clock } from 'lucide-react'
import { Alert, Button, Card } from '../../components/ui'
import { api, type StartedTest, type TestKind } from '../../lib/api'
import { TEST_BY_KIND, isTestKind } from '../../lib/tests'
import { ChoiceTest, MathTest, MemoryTest } from './Runners'
import { ReadingTest } from './ReadingTest'

const INSTRUCTIONS: Record<TestKind, string[]> = {
  math: ['Solve each question and type the answer.', 'Work at a comfortable pace; time taken is recorded.'],
  grammar: ['Choose the word or phrase that correctly completes each sentence.'],
  reading: [
    'You will see a short passage. Press "Start reading" and read it aloud clearly.',
    'Your browser will ask to use the microphone. Speech recognition works best in Chrome or Edge.',
  ],
  memory: ['Six digits will appear for a few seconds.', 'When they disappear, type them back in the same order.'],
  scenario: ['Read the short story carefully.', 'Then answer the questions about it.'],
}

export interface RunnerProps<T = StartedTest> {
  test: T
  busy: boolean
  onSubmit: (payload: unknown) => void
}

export default function TestRunner() {
  const { kind } = useParams()
  const navigate = useNavigate()
  const [started, setStarted] = useState<StartedTest | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isTestKind(kind)) return <Navigate to="/tests" replace />
  const info = TEST_BY_KIND[kind]

  async function start() {
    setBusy(true)
    setError(null)
    try {
      setStarted(await api.startTest(kind as TestKind))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  async function submit(payload: unknown) {
    if (!started) return
    setBusy(true)
    setError(null)
    try {
      await api.submitTest(started.kind, started.id, payload)
      navigate(`/tests/${started.kind}/${started.id}/result`, { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  const runnerProps = { busy, onSubmit: submit }

  return (
    <div className="mx-auto max-w-2xl">
      <Link to="/tests" className="mb-6 inline-flex min-h-11 items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900">
        <ArrowLeft className="size-4" aria-hidden /> All assessments
      </Link>
      <div className="mb-6 flex items-center gap-3">
        <span className="flex size-10 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
          <info.icon className="size-5" aria-hidden />
        </span>
        <div>
          <h1 className="text-2xl font-semibold">{info.name} assessment</h1>
          <p className="text-sm text-slate-500">{info.area}</p>
        </div>
      </div>

      {error && <div className="mb-4"><Alert>{error}</Alert></div>}

      {!started ? (
        <Card>
          <h2 className="font-semibold">Before you start</h2>
          <ul className="mt-3 list-disc space-y-1.5 pl-5 text-slate-600">
            {INSTRUCTIONS[kind].map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <div className="mt-6 flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-sm text-slate-500">
              <Clock className="size-4" aria-hidden /> About {info.minutes} min
            </span>
            <Button onClick={start} loading={busy}>
              Start test
            </Button>
          </div>
        </Card>
      ) : kind === 'math' ? (
        <MathTest test={started} {...runnerProps} />
      ) : kind === 'reading' ? (
        <ReadingTest test={started} {...runnerProps} />
      ) : kind === 'memory' ? (
        <MemoryTest test={started} {...runnerProps} />
      ) : (
        <ChoiceTest test={started} {...runnerProps} />
      )}
    </div>
  )
}
