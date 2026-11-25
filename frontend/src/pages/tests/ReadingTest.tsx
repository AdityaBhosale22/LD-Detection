import { useEffect, useRef, useState } from 'react'
import { Mic, RotateCcw, Square } from 'lucide-react'
import { Alert, Button, Card, Textarea } from '../../components/ui'
import type { RunnerProps } from './TestRunner'

// Minimal typing for the Web Speech API (not in TypeScript's DOM lib yet).
interface SpeechRecognitionResultEvent {
  resultIndex: number
  results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }>
}
interface SpeechRecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null
  onerror: ((event: { error: string }) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike

function getRecognizer(): SpeechRecognitionCtor | undefined {
  const w = window as unknown as { SpeechRecognition?: SpeechRecognitionCtor; webkitSpeechRecognition?: SpeechRecognitionCtor }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition
}

type Phase = 'ready' | 'listening' | 'done'

export function ReadingTest({ test, busy, onSubmit }: RunnerProps) {
  const Recognizer = getRecognizer()
  const [phase, setPhase] = useState<Phase>('ready')
  const [finalText, setFinalText] = useState('')
  const [interim, setInterim] = useState('')
  const [typed, setTyped] = useState('')
  const [micError, setMicError] = useState<string | null>(null)
  const recognizer = useRef<SpeechRecognitionLike | null>(null)
  const startedAt = useRef(Date.now())
  const seconds = useRef(0)

  useEffect(() => () => recognizer.current?.stop(), [])

  function start() {
    if (!Recognizer) return
    const rec = new Recognizer()
    rec.lang = 'en-US'
    rec.continuous = true
    rec.interimResults = true
    rec.onresult = (event) => {
      let finals = ''
      let pending = ''
      for (let i = 0; i < event.results.length; i++) {
        const r = event.results[i]
        if (r.isFinal) finals += r[0].transcript + ' '
        else pending += r[0].transcript
      }
      setFinalText(finals.trim())
      setInterim(pending)
    }
    rec.onerror = (event) => {
      setMicError(event.error === 'not-allowed' ? 'Microphone access was blocked. Allow it in your browser and try again.' : `Speech recognition error: ${event.error}`)
    }
    rec.onend = () => {
      seconds.current = Math.max(1, Math.round((Date.now() - startedAt.current) / 1000))
      setInterim('')
      setPhase('done')
    }
    recognizer.current = rec
    setFinalText('')
    setMicError(null)
    startedAt.current = Date.now()
    rec.start()
    setPhase('listening')
  }

  function stop() {
    recognizer.current?.stop()
  }

  const passage = (
    <Card>
      <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">Read this aloud</p>
      <p className="mt-3 font-display text-2xl leading-relaxed sm:text-3xl">{test.passage}</p>
    </Card>
  )

  // Fallback for browsers without speech recognition (e.g. Firefox): type what was read.
  if (!Recognizer) {
    return (
      <div className="space-y-4">
        {passage}
        <Card>
          <Alert tone="info">
            Speech recognition isn't available in this browser. For the real test use Chrome or Edge. You can still type
            the passage below to try it out.
          </Alert>
          <form
            className="mt-4 space-y-4"
            onSubmit={(e) => {
              e.preventDefault()
              onSubmit({ transcript: typed, reading_seconds: Math.round((Date.now() - startedAt.current) / 1000) })
            }}
          >
            <Textarea label="What you read" name="transcript" value={typed} onChange={(e) => setTyped(e.target.value)} />
            <div className="flex justify-end">
              <Button type="submit" loading={busy} disabled={!typed.trim()}>
                Submit
              </Button>
            </div>
          </form>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {passage}
      <Card>
        {micError && <div className="mb-4"><Alert>{micError}</Alert></div>}
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm text-slate-600" aria-live="polite">
            {phase === 'ready' && 'Press start, then read the passage at your normal pace.'}
            {phase === 'listening' && (
              <span className="flex items-center gap-2">
                <span className="size-2.5 animate-pulse rounded-full bg-red-500" aria-hidden /> Listening… press stop when you finish.
              </span>
            )}
            {phase === 'done' && `Recorded in ${seconds.current}s.`}
          </p>
          {phase === 'listening' ? (
            <Button variant="secondary" onClick={stop}>
              <Square className="size-4" aria-hidden /> Stop
            </Button>
          ) : phase === 'ready' ? (
            <Button onClick={start}>
              <Mic className="size-4" aria-hidden /> Start reading
            </Button>
          ) : (
            <Button variant="ghost" onClick={start}>
              <RotateCcw className="size-4" aria-hidden /> Try again
            </Button>
          )}
        </div>

        {(finalText || interim) && (
          <div className="mt-4 rounded-lg bg-slate-50 p-4">
            <p className="text-xs font-medium tracking-wide text-slate-500 uppercase">What we heard</p>
            <p className="mt-1.5">
              {finalText} <span className="text-slate-400">{interim}</span>
            </p>
          </div>
        )}

        {phase === 'done' && (
          <div className="mt-6 flex justify-end">
            <Button
              loading={busy}
              disabled={!finalText}
              onClick={() => onSubmit({ transcript: finalText, reading_seconds: seconds.current })}
            >
              Submit reading
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}
