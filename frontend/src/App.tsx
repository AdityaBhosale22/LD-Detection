import { Route, Routes } from 'react-router'
import { AppLayout } from './components/Layout'
import { ButtonLink } from './components/ui'
import { Login, Register } from './pages/Auth'
import Dashboard from './pages/Dashboard'
import Intake from './pages/Intake'
import Landing from './pages/Landing'
import Recommendations from './pages/Recommendations'
import Tests from './pages/Tests'
import Result from './pages/tests/Result'
import TestRunner from './pages/tests/TestRunner'

function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="text-slate-600">The page you are looking for doesn't exist.</p>
      <ButtonLink to="/">Go home</ButtonLink>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/intake" element={<Intake />} />
        <Route path="/tests" element={<Tests />} />
        <Route path="/tests/:kind" element={<TestRunner />} />
        <Route path="/tests/:kind/:id/result" element={<Result />} />
        <Route path="/recommendations" element={<Recommendations />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
