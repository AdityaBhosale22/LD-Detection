import { BookOpen, Brain, Calculator, MessageSquareText, SpellCheck, type LucideIcon } from 'lucide-react'
import type { TestKind, TestResult } from './api'

export interface TestInfo {
  kind: TestKind
  name: string
  area: string
  description: string
  minutes: number
  icon: LucideIcon
}

export const TESTS: TestInfo[] = [
  {
    kind: 'math',
    name: 'Math',
    area: 'Numeracy',
    description: 'Ten quick addition and subtraction questions.',
    minutes: 3,
    icon: Calculator,
  },
  {
    kind: 'grammar',
    name: 'Grammar',
    area: 'Language',
    description: 'Pick the word that completes each sentence.',
    minutes: 2,
    icon: SpellCheck,
  },
  {
    kind: 'reading',
    name: 'Reading',
    area: 'Reading fluency',
    description: 'Read a short passage aloud. We measure speed and accuracy.',
    minutes: 2,
    icon: BookOpen,
  },
  {
    kind: 'memory',
    name: 'Memory',
    area: 'Working memory',
    description: 'Remember a sequence of six digits and type it back.',
    minutes: 1,
    icon: Brain,
  },
  {
    kind: 'scenario',
    name: 'Comprehension',
    area: 'Reading comprehension',
    description: 'Read a short story and answer questions about it.',
    minutes: 2,
    icon: MessageSquareText,
  },
]

export const TEST_BY_KIND = Object.fromEntries(TESTS.map((t) => [t.kind, t])) as Record<TestKind, TestInfo>

export function isTestKind(value: string | undefined): value is TestKind {
  return !!value && value in TEST_BY_KIND
}

export function summarize(result: TestResult) {
  if (result.wpm !== undefined && result.accuracy !== undefined) {
    return `${Math.round(result.wpm)} wpm · ${Math.round(result.accuracy * 100)}% accuracy`
  }
  return `${result.num_correct} / ${result.num_total} correct`
}

export function formatDuration(seconds: number) {
  if (seconds < 60) return `${seconds}s`
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
}
