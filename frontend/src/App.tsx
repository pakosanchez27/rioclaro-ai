
import { Navigate, Route, Routes } from 'react-router-dom'
import { useEffect, useState, type FormEvent } from 'react'
import axios from 'axios'
import { evaluatorSession, loginEvaluator } from './lib/api'

import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import FacturasPage from './pages/FacturasPage'
import FacturaDetallePage from './pages/FacturaDetallePage'
import AnalizarFacturaPage from './pages/AnalizarFacturaPage'
import AsistentePage from './pages/AsistentePage'
import PedidosQuejasPage from './pages/PedidosQuejasPage'
import ReportesPage from './pages/ReportesPage'
import PlaceholderPage from './pages/PlaceholderPage'

export default function App() {
  const [authenticated, setAuthenticated] = useState(evaluatorSession.active)
  const [code, setCode] = useState('')
  const [error, setError] = useState(sessionStorage.getItem('evaluator_token') && !evaluatorSession.active ? 'La sesión expiró. Ingresa de nuevo.' : '')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const expired = () => { setAuthenticated(false); setError('La sesión expiró. Ingresa de nuevo.') }
    window.addEventListener('evaluator-session-expired', expired)
    return () => window.removeEventListener('evaluator-session-expired', expired)
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await loginEvaluator(code)
      setCode('')
      setAuthenticated(true)
    } catch (err) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined
      setError(status === 429 ? 'Demasiados intentos. Intenta de nuevo en 15 minutos.'
        : status === 503 ? 'El acceso de evaluación está temporalmente suspendido.'
        : 'Credencial incorrecta.')
    } finally { setBusy(false) }
  }

  if (!authenticated) return (
    <main className="flex min-h-screen items-center justify-center bg-[#F5F7FB] px-5 py-10">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-7 shadow-xl sm:p-10">
        <div className="mb-7 flex size-12 items-center justify-center rounded-2xl bg-teal-400 text-slate-950 text-2xl">✦</div>
        <h1 className="text-2xl font-bold text-slate-950">Río Claro AI</h1>
        <p className="mt-2 text-sm text-slate-600">Acceso temporal para evaluadores</p>
        <form onSubmit={submit} className="mt-8 space-y-5">
          <label className="block text-sm font-medium text-slate-800" htmlFor="evaluation-code">Credencial de evaluación</label>
          <input id="evaluation-code" type="password" autoComplete="off" required value={code} onChange={event => setCode(event.target.value)} className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-200" />
          {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
          <button disabled={busy} className="w-full rounded-xl bg-slate-950 px-4 py-3 font-semibold text-white hover:bg-slate-800 disabled:opacity-50">{busy ? 'Verificando…' : 'Ingresar'}</button>
        </form>
        <p className="mt-6 text-xs text-slate-500">Las funciones de IA tienen límites diarios y pueden estar temporalmente suspendidas.</p>
      </div>
    </main>
  )
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />

        <Route path="facturas" element={<FacturasPage />} />

        <Route
          path="facturas/:factura_id"
          element={<FacturaDetallePage />}
        />

        <Route
          path="analizar"
          element={<AnalizarFacturaPage />}
        />

        <Route path="asistente" element={<AsistentePage />} />
        <Route path="pedidos-quejas" element={<PedidosQuejasPage />} />
        <Route path="reportes" element={<ReportesPage />} />

        <Route
          path="revisiones"
          element={
            <PlaceholderPage
              title="Revisiones"
              description="Aprobación y rechazo de facturas pendientes."
            />
          }
        />

        <Route
          path="historial"
          element={
            <PlaceholderPage
              title="Historial"
              description="Auditoría y trazabilidad de las revisiones."
            />
          }
        />

        <Route
          path="configuracion"
          element={
            <PlaceholderPage
              title="Configuración"
              description="Perfil y preferencias del sistema."
            />
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
