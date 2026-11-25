import { useEffect, useState, type FormEvent } from 'react'
import { cx } from '../../lib/cx'
import { Button, Card } from '../../components/ui'
import type { Question } from '../../lib/api'
import type { RunnerProps } from './TestRunner'

type MathQuestion = { a: number; b: number; op: '+' | '-' }

function SubmitBar({ answered, total, busy }: { answered: number; total: number; busy: boolean }) {
  return (
    <div className="mt-6 flex items-center justify-between">
      <span className="text-sm text-slate-500" aria-live="polite">
        {answered} of {total} answered
      </span>
      <Button type="submit" loading={busy}>
        Submit answers
      </Button>
    </div>
  )
}

export function MathTest({ test, busy, onSubmit }: RunnerProps) {
  const questions = (test.questions ?? []) as MathQuestion[]
  const [answers, setAnswers] = useState<string[]>(() => questions.map(() => ''))

  function submit(e: FormEvent) {
    e.preventDefault()
    onSubmit({ answers: answers.map((a) => (a.trim() === '' ? null : Number(a))) })
  }

  return (
    <form onSubmit={submit}>
      <Card>
        <ol className="grid gap-3 sm:grid-cols-2">
          {questions.map((q, i) => (
            <li key={i} className="flex items-center gap-3 rounded-lg border border-slate-200 px-4 py-3">
              <span className="w-6 text-sm text-slate-400">{i + 1}.</span>
              <label htmlFor={`q${i}`} className="flex-1 font-display text-lg tabular-nums">
                {q.a} {q.op === '-' ? '−' : '+'} {q.b} =
              </label>
              <input
                id={`q${i}`}
                type="text"
                inputMode="numeric"
                pattern="-?[0-9]*"
                autoComplete="off"
                value={answers[i]}
                onChange={(e) => setAnswers((prev) => prev.map((v, j) => (j === i ? e.target.value.replace(/[^0-9-]/g, '') : v)))}
                className="w-20 rounded-lg border border-slate-300 px-3 py-2 text-center text-lg tabular-nums focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20"
              />
            </li>
          ))}
        </ol>
        <SubmitBar answered={answers.filter((a) => a.trim() !== '').length} total={questions.length} busy={busy} />
      </Card>
    </form>
  )
}

/** Multiple-choice runner used by the grammar and comprehension (scenario) tests. */
export function ChoiceTest({ test, busy, onSubmit }: RunnerProps) {
  const questions = (test.questions ?? []) as Question[]
  const [answers, setAnswers] = useState<(string | null)[]>(() => questions.map(() => null))

  function submit(e: FormEvent) {
    e.preventDefault()
    onSubmit({ answers })
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      {test.text && (
        <Card className="bg-slate-50">
          <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Story</p>
          <p className="mt-2 text-lg leading-relaxed">{test.text}</p>
        </Card>
      )}
      <Card>
        <div className="space-y-6">
          {questions.map((q, i) => (
            <fieldset key={i}>
              <legend className="font-medium">
                <span className="text-slate-400">{i + 1}.</span> {q.prompt}
              </legend>
              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                {q.options.map((option) => (
                  <label
                    key={option}
                    className={cx(
                      'flex min-h-11 cursor-pointer items-center rounded-lg border border-slate-300 px-3 py-2 text-sm transition-colors hover:bg-slate-50',
                      'has-[:checked]:border-brand-600 has-[:checked]:bg-brand-50 has-[:checked]:font-medium has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-brand-600',
                    )}
                  >
                    <input
                      type="radio"
                      name={`q${i}`}
                      value={option}
                      checked={answers[i] === option}
                      onChange={() => setAnswers((prev) => prev.map((v, j) => (j === i ? option : v)))}
                      className="sr-only"
                    />
                    {option}
                  </label>
                ))}
              </div>
            </fieldset>
          ))}
        </div>
        <SubmitBar answered={answers.filter(Boolean).length} total={questions.length} busy={busy} />
      </Card>
    </form>
  )
}

export function MemoryTest({ test, busy, onSubmit }: RunnerProps) {
  const sequence = test.sequence ?? []
  const [remaining, setRemaining] = useState(test.display_seconds ?? 5)
  const [value, setValue] = useState('')
  const showing = remaining > 0

  useEffect(() => {
    if (!showing) return
    const id = window.setTimeout(() => setRemaining((r) => r - 1), 1000)
    return () => window.clearTimeout(id)
  }, [remaining, showing])

  function submit(e: FormEvent) {
    e.preventDefault()
    onSubmit({ response: value.split('').map(Number) })
  }

  return (
    <Card className="text-center">
      {showing ? (
        <>
          <p className="text-sm text-slate-500" aria-live="polite">
            Memorise these digits · {remaining}s
          </p>
          <p className="mt-6 mb-4 font-display text-5xl font-semibold tracking-[0.3em] tabular-nums sm:text-6xl">
            {sequence.join('')}
          </p>
        </>
      ) : (
        <form onSubmit={submit}>
          <label htmlFor="recall" className="text-sm text-slate-600">
            Type the {sequence.length} digits in the same order
          </label>
          <input
            id="recall"
            autoFocus
            inputMode="numeric"
            autoComplete="off"
            maxLength={sequence.length}
            value={value}
            onChange={(e) => setValue(e.target.value.replace(/\D/g, ''))}
            className="mx-auto mt-4 block w-full max-w-xs rounded-lg border border-slate-300 px-3 py-3 text-center font-display text-3xl tracking-[0.3em] tabular-nums focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20"
          />
          <Button type="submit" loading={busy} disabled={value.length === 0} className="mt-6">
            Submit
          </Button>
        </form>
      )}
    </Card>
  )
}
