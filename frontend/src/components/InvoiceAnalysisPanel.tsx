import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  Clock3,
  FileSearch,
  Sparkles,
} from 'lucide-react'

import { getInvoiceAnalysis } from '../lib/api'
import { formatMoney } from '../lib/invoiceFormat'

interface Props {
  invoiceId: string
}

export default function InvoiceAnalysisPanel({ invoiceId }: Props) {
  const { data, isPending, isError } = useQuery({
    queryKey: ['invoice-analysis', invoiceId],
    queryFn: () => getInvoiceAnalysis(invoiceId),
  })

  if (isPending) {
    return (
      <div className="rounded-2xl bg-white p-6 text-sm text-slate-500">
        Cargando análisis guardado...
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-red-100 bg-white p-6 text-sm text-red-700">
        No fue posible consultar el análisis de esta factura.
      </div>
    )
  }

  const saved = data.data

  if (!saved) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <FileSearch className="text-slate-400" size={26} />
        <h2 className="mt-3 font-bold text-slate-900">
          Sin análisis de IA guardado
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Esta factura puede provenir de los datos de demostración.
          No necesita volver a procesarse para consultar su información básica.
        </p>
      </div>
    )
  }

  const { extraction, analysis } = saved
  const financial = analysis.financial_validation

  const money = (value: number | null) =>
    value === null
      ? 'No detectado'
      : formatMoney(value, extraction.currency ?? 'MXN')

  return (
    <section className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <BrainCircuit size={23} className="text-teal-700" />
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              Análisis inteligente
            </h2>
            <p className="text-xs text-slate-500">
              Recuperado de SQLite, sin realizar otra llamada a Azure.
            </p>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {[
            ['Subtotal', money(extraction.subtotal)],
            ['Impuestos', money(extraction.tax)],
            ['Total', money(extraction.total)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="mt-2 font-bold text-slate-800">{value}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 flex items-start gap-2 rounded-xl bg-slate-50 p-4">
          {financial.is_consistent === true ? (
            <CheckCircle2 className="shrink-0 text-emerald-600" size={21} />
          ) : financial.is_consistent === false ? (
            <AlertCircle className="shrink-0 text-red-600" size={21} />
          ) : (
            <Clock3 className="shrink-0 text-amber-600" size={21} />
          )}

          <div>
            <p className="text-sm font-semibold text-slate-800">
              {financial.is_consistent === true
                ? 'Los importes son consistentes'
                : financial.is_consistent === false
                  ? 'Se detectó una diferencia'
                  : 'Validación financiera incompleta'}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Comprobación matemática realizada mediante Python.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="font-bold text-slate-900">
          Hallazgos detectados
        </h3>

        {analysis.duplicate_check?.status === 'possible' && (
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
            <p className="font-semibold">Posible duplicado: revisión necesaria</p>
            {analysis.duplicate_check.related_invoices.map((related) => (
              <p key={related.invoice_id} className="mt-2">
                <Link className="font-semibold underline" to={`/facturas/${encodeURIComponent(related.invoice_id)}`}>
                  Factura {related.invoice_id}
                </Link>: {related.reason}
              </p>
            ))}
          </div>
        )}

        {analysis.findings.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">
            No se encontraron hallazgos con las reglas actuales.
          </p>
        ) : (
          <div className="mt-4 space-y-3">
            {analysis.findings.map((finding, index) => (
              <div
                key={`${finding.field}-${index}`}
                className="rounded-xl border border-amber-100 bg-amber-50 p-4"
              >
                <p className="text-sm font-semibold text-amber-900">
                  {finding.message}
                </p>
                <p className="mt-1 text-xs text-amber-700">
                  Campo: {finding.field} · Severidad: {finding.severity}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <Sparkles className="text-teal-700" size={21} />
          <h3 className="font-bold text-slate-900">
            Observaciones de GPT-5 mini
          </h3>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-slate-700">
          {analysis.ai_analysis.summary}
        </p>

        <h4 className="mt-6 text-sm font-bold text-slate-900">
          Recomendaciones
        </h4>

        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-600">
          {analysis.ai_analysis.review_steps.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>

        <p className="mt-5 rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
          Las recomendaciones son orientativas. No constituyen
          una validación fiscal ni una aprobación automática.
        </p>
      </div>
    </section>
  )
}
