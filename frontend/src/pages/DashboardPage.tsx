
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  FileText,
  ScanLine,
  Server,
  Sparkles,
} from 'lucide-react'
import { getHealth } from '../lib/api'
import InvoiceStatsPanel from '../components/InvoiceStatsPanel'

function ApiStatus() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['api-health'],
    queryFn: getHealth,
    retry: 1,
    refetchInterval: 30000,
  })

  const connected = data?.status === 'ok'

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-teal-50 p-3 text-teal-700">
          <Server size={22} />
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="font-bold text-slate-900">
            Estado de la API
          </h3>
          <p className="text-sm text-slate-500">
            Azure Functions · API local
          </p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        {isPending ? (
          <span className="text-sm text-slate-500">
            Comprobando conexión...
          </span>
        ) : isError || !connected ? (
          <span className="inline-flex items-center gap-2 rounded-full bg-red-50 px-3 py-1.5 text-sm font-semibold text-red-700">
            <CircleAlert size={16} />
            API no disponible
          </span>
        ) : (
          <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-semibold text-emerald-700">
            <CheckCircle2 size={16} />
            API conectada
          </span>
        )}

        {connected && (
          <span className="text-xs text-slate-400">
            Versión {data.version}
          </span>
        )}
      </div>

      {isError && (
        <p className="mt-3 text-xs text-slate-500">
          Comprueba que Azure Functions esté ejecutándose y que la API esté configurada.
        </p>
      )}
    </div>
  )
}

export default function DashboardPage() {
  return (
    <div className="space-y-7">
      <div>
        <p className="text-sm font-semibold text-teal-700">
          Vista general
        </p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">
          Dashboard
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Supervisa la actividad y el procesamiento de facturas.
        </p>
      </div>

      <section className="relative overflow-hidden rounded-3xl bg-[#101C32] p-7 text-white md:p-9">
        <div className="absolute -right-15 -top-20 size-70 rounded-full bg-teal-400/10 blur-3xl" />

        <div className="relative z-10 max-w-2xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-teal-300/20 bg-teal-300/10 px-3 py-1.5 text-xs font-semibold text-teal-200">
            <Sparkles size={14} />
            Inteligencia documental
          </div>

          <h2 className="text-2xl font-bold leading-tight md:text-3xl">
            Gestiona tus facturas con inteligencia artificial
          </h2>

          <p className="mt-3 text-sm leading-relaxed text-slate-300">
            Extrae información con Azure Document Intelligence,
            identifica inconsistencias y recibe observaciones
            generadas por GPT-5 mini.
          </p>

          <Link
            to="/analizar"
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-teal-400 px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-teal-300"
          >
            Ir al módulo de análisis
            <ArrowRight size={17} />
          </Link>
        </div>
      </section>

      <InvoiceStatsPanel />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <ApiStatus />

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-slate-100 p-3 text-slate-700">
              <ScanLine size={22} />
            </div>

            <div>
              <h3 className="font-bold text-slate-900">
                Procesamiento inteligente
              </h3>
              <p className="text-sm text-slate-500">
                Servicios de inteligencia artificial
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-3 text-sm">
            <div className="flex justify-between gap-3">
              <span className="text-slate-500">
                Extracción documental
              </span>
              <span className="font-semibold text-slate-700">
                Document Intelligence
              </span>
            </div>

            <div className="flex justify-between gap-3">
              <span className="text-slate-500">
                Análisis de IA
              </span>
              <span className="font-semibold text-slate-700">
                GPT-5 mini
              </span>
            </div>
          </div>

          <p className="mt-5 rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
            Ambos servicios se probaron desde el backend.
            Este panel todavía no consulta su estado en tiempo real.
          </p>
        </div>
      </div>
      <section className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-11 text-center">
        <FileText className="mx-auto text-slate-300" size={36} />
        
        <h3 className="mt-4 text-base font-bold text-slate-800">
          Actividad reciente
        </h3>

        <p className="mx-auto mt-2 max-w-md text-sm text-slate-500">
          Consulta el listado de facturas para ver los documentos registrados.
        </p>
      </section>
    </div>
  )
}
