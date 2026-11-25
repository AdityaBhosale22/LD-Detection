import { useState, type FormEvent } from 'react'
import { cx } from '../lib/cx'
import { useNavigate } from 'react-router'
import { Alert, Button, Card, Input, PageHeader, Select, Spinner, Textarea } from '../components/ui'
import { ApiError, api, type Intake as IntakeData } from '../lib/api'
import { useLoad } from '../lib/useLoad'

const ATTENTION = [
  { value: 'low', label: 'Low', hint: 'Loses focus quickly' },
  { value: 'medium', label: 'Medium', hint: 'Focuses with breaks' },
  { value: 'high', label: 'High', hint: 'Stays on task easily' },
] as const

export default function Intake() {
  const { data: existing, loading } = useLoad(api.getIntake)
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [fields, setFields] = useState<Record<string, string>>({})

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const form = new FormData(e.currentTarget)
    setBusy(true)
    setError(null)
    setFields({})
    try {
      await api.saveIntake({
        age: Number(form.get('age')),
        gender: form.get('gender') as IntakeData['gender'],
        attention_span: form.get('attention_span') as IntakeData['attention_span'],
        reading_difficulties: form.get('reading_difficulties') === 'on',
        academic_history: String(form.get('academic_history') ?? ''),
        learning_issues_notes: String(form.get('learning_issues_notes') ?? ''),
      })
      await api.runPrediction()
      navigate('/dashboard')
    } catch (err) {
      if (err instanceof ApiError) setFields(err.fields)
      setError((err as Error).message)
      setBusy(false)
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        title="Student profile"
        description="A few details about the student. They are used by the screening model and shown in the report."
      />
      <Card>
        <form onSubmit={onSubmit} className="space-y-6" noValidate>
          {error && <Alert>{error}</Alert>}
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Age"
              name="age"
              type="number"
              inputMode="numeric"
              min={4}
              max={25}
              required
              defaultValue={existing?.age}
              error={fields.age}
            />
            <Select label="Gender" name="gender" defaultValue={existing?.gender ?? 'female'} error={fields.gender}>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="other">Other / prefer not to say</option>
            </Select>
          </div>

          <fieldset>
            <legend className="mb-1.5 text-sm font-medium text-slate-800">Attention span</legend>
            <div className="grid gap-2 sm:grid-cols-3">
              {ATTENTION.map((opt) => (
                <label
                  key={opt.value}
                  className={cx(
                    'flex cursor-pointer flex-col rounded-lg border border-slate-300 px-3 py-2.5 transition-colors',
                    'has-[:checked]:border-brand-600 has-[:checked]:bg-brand-50 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-brand-600',
                  )}
                >
                  <input
                    type="radio"
                    name="attention_span"
                    value={opt.value}
                    defaultChecked={(existing?.attention_span ?? 'medium') === opt.value}
                    className="sr-only"
                  />
                  <span className="text-sm font-medium">{opt.label}</span>
                  <span className="text-xs text-slate-500">{opt.hint}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              name="reading_difficulties"
              defaultChecked={existing?.reading_difficulties}
              className="mt-0.5 size-5 rounded border-slate-300 accent-brand-700"
            />
            <span>
              <span className="block text-sm font-medium">Has noticeable reading difficulties</span>
              <span className="block text-sm text-slate-500">For example skipping words, slow reading or mixing up letters.</span>
            </span>
          </label>

          <Textarea
            label="Academic history (optional)"
            name="academic_history"
            defaultValue={existing?.academic_history}
            placeholder="Grade, subjects that are easy or hard…"
          />
          <Textarea
            label="Other notes (optional)"
            name="learning_issues_notes"
            defaultValue={existing?.learning_issues_notes}
            placeholder="Anything a teacher or parent has noticed"
          />

          <div className="flex justify-end">
            <Button type="submit" loading={busy}>
              Save and run screening
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}
