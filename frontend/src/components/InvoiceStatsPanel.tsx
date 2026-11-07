import { useQuery } from '@tanstack/react-query'
import {
  FileText,
  Clock3,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'

import { getInvoiceStats } from '../lib/api'

export default function InvoiceStatsPanel() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['invoice-stats'],
    queryFn: getInvoiceStats,
  })

  if (isPending) {
    return (
      <div className="rounded-2xl bg-white p-6 text-sm text-slate-500">
        Cargando indicadores...
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center gap-2 rounded-2xl border border-red-100 bg-white p-6 text-sm text-red-700">
        <AlertCircle size={18} />
        No fue posible consultar las estadísticas.
      </div>
    )
  }

  const metrics = [
    {
      label: 'Total de facturas',
      value: data.total_invoices,
      icon: FileText,
    },
    {
      label: 'Pendientes de revisión',
      value: data.pending_review,
      icon: Clock3,
    },
    {
      label: 'Facturas validadas',
      value: data.validated,
      icon: CheckCircle2,
    },
  ]

  return (
    <section>
      <h2 className="mb-4 text-lg font-bold text-slate-900">
        Indicadores reales
      </h2>

      <div className="grid gap-4 md:grid-cols-3">
        {metrics.map(({ label, value, icon: Icon }) => (
          <div
            key={label}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="mb-5 flex size-11 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
              <Icon size={21} />
            </div>

            <p className="text-sm text-slate-500">
              {label}
            </p>

            <p className="mt-2 text-3xl font-bold text-slate-900">
              {value ?? 0}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-3 text-xs text-slate-400">
        Los importes no se agregan entre monedas diferentes.
      </p>
    </section>
  )
}
