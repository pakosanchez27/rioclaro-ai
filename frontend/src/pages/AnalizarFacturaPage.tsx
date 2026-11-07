import { useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileText,
  LoaderCircle,
  RefreshCw,
  ScanLine,
  ShieldAlert,
  Sparkles,
  UploadCloud,
  X,
} from 'lucide-react'

import { analyzeInvoice } from '../lib/api'
import type { AnalyzeInvoiceResponse } from '../lib/api'
import { formatMoney, formatInvoiceDate } from '../lib/invoiceFormat'

const MAX_FILE_SIZE = 4_000_000
const ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg']

function getErrorMessage(error: Error): string {
  if (axios.isAxiosError<{ error?: string; related_invoice_id?: string }>(error)) {
    const status = error.response?.status
    const serverMessage = error.response?.data?.error

    if (status === 401) return 'La API solicita autenticación. Verifica el modo de demostración.'
    if (status === 403) return 'No tienes permisos para analizar facturas.'
    if (status === 413) return 'El archivo supera el tamaño permitido.'
    if (status === 415) return 'El formato del documento no es compatible.'
    if (status === 409) return serverMessage ?? 'Esta factura ya fue registrada o está en procesamiento.'
    if (status === 429) return 'Se agotó la cuota diaria de análisis. Inténtalo mañana.'
    if (status === 503) return 'El análisis está suspendido temporalmente.'
    if (status === 422) return serverMessage ?? 'No se pudieron identificar los datos necesarios.'
    if (status === 502) return 'Azure no pudo completar el análisis. Inténtalo después.'

    if (error.code === 'ECONNABORTED') {
      return 'El análisis tardó demasiado. Comprueba si la factura llegó a guardarse antes de volver a enviarla.'
    }

    return serverMessage ?? 'No fue posible conectar con la API.'
  }

  return error.message || 'Ocurrió un error inesperado.'
}

function ResultPanel({ result }: { result: AnalyzeInvoiceResponse }) {
  const { extraction, analysis } = result
  const financial = analysis.financial_validation
  const currency = extraction.currency ?? 'MXN'

  const money = (value: number | null) =>
    value === null ? 'No detectado' : formatMoney(value, currency)

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 shrink-0 text-emerald-700" size={24} />
          <div className="flex-1">
            <h2 className="font-bold text-emerald-900">
              Análisis completado y guardado
            </h2>
            <p className="mt-1 text-sm text-emerald-800">
              La factura se registró como pendiente de revisión.
            </p>
            <Link
              to={`/facturas/${encodeURIComponent(result.invoice_id)}`}
              className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-emerald-900 underline"
            >
              Abrir factura guardada
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">
          Información extraída
        </h2>

        <dl className="mt-5 grid gap-5 sm:grid-cols-2">
          {[
            ['Proveedor', extraction.supplier_name ?? 'No detectado'],
            ['Identificador fiscal', extraction.supplier_tax_id ?? 'No detectado'],
            ['Número de factura', extraction.invoice_number ?? 'No detectado'],
            ['Fecha', formatInvoiceDate(extraction.invoice_date)],
          ].map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                {label}
              </dt>
              <dd className="mt-1 break-words text-sm font-semibold text-slate-800">
                {value}
              </dd>
            </div>
          ))}
        </dl>

        <div className="mt-6 grid gap-3 border-t border-slate-100 pt-5 sm:grid-cols-3">
          {[
            ['Subtotal', money(extraction.subtotal)],
            ['Impuestos', money(extraction.tax)],
            ['Total', money(extraction.total)],
          ].map(([label, value]) => (
            <div key={label} className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs text-slate-500">{label}</p>
              <p className="mt-1 break-words font-bold text-slate-900">
                {value}
              </p>
            </div>
          ))}
        </div>

        <p className="mt-4 text-xs text-slate-400">
          Extraído mediante {extraction.metadata.model}.
          Páginas analizadas: {extraction.metadata.pages_analyzed}.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">
          Validación financiera
        </h2>

        <div className="mt-4 flex items-center gap-2">
          {financial.is_consistent === true ? (
            <>
              <CheckCircle2 className="text-emerald-600" size={20} />
              <span className="font-semibold text-emerald-700">
                Los importes son consistentes
              </span>
            </>
          ) : financial.is_consistent === false ? (
            <>
              <AlertCircle className="text-red-600" size={20} />
              <span className="font-semibold text-red-700">
                Se detectó una diferencia en los importes
              </span>
            </>
          ) : (
            <>
              <Clock3 className="text-amber-600" size={20} />
              <span className="font-semibold text-amber-700">
                No fue posible completar la validación
              </span>
            </>
          )}
        </div>

        <p className="mt-3 text-sm text-slate-500">
          Esta comprobación utiliza reglas de Python, no cálculos
          generados por inteligencia artificial.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <ShieldAlert className="text-amber-600" size={21} />
          <h2 className="text-lg font-bold text-slate-900">
            Hallazgos
          </h2>
        </div>

        {analysis.findings.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">
            No se detectaron inconsistencias con las reglas actuales.
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

      {analysis.duplicate_check?.status === 'possible' && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <h2 className="font-bold text-amber-900">Posible duplicado</h2>
          <p className="mt-1 text-sm text-amber-800">
            Revisa estas facturas antes de aprobar el documento.
          </p>
          <ul className="mt-3 space-y-2">
            {analysis.duplicate_check.related_invoices.map((related) => (
              <li key={related.invoice_id} className="text-sm text-amber-900">
                <Link className="font-semibold underline" to={`/facturas/${encodeURIComponent(related.invoice_id)}`}>
                  Ver factura relacionada
                </Link>
                {' · '}{related.reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <Sparkles className="text-teal-600" size={22} />
          <h2 className="text-lg font-bold text-slate-900">
            Observaciones de la IA
          </h2>
        </div>

        <p className="mt-4 text-sm leading-relaxed text-slate-700">
          {analysis.ai_analysis.summary}
        </p>

        <h3 className="mt-6 text-sm font-bold text-slate-900">
          Recomendaciones de revisión
        </h3>

        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-600">
          {analysis.ai_analysis.review_steps.map((step, index) => (
            <li key={index}>{step}</li>
          ))}
        </ol>

        <p className="mt-6 rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
          Estas recomendaciones son orientativas. La validación y aprobación
          final corresponde a una persona.
        </p>
      </div>
    </div>
  )
}

export default function AnalizarFacturaPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [validationError, setValidationError] = useState('')

  const mutation = useMutation({
    mutationFn: analyzeInvoice,
    retry: false,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['invoices'] }),
        queryClient.invalidateQueries({ queryKey: ['invoice-stats'] }),
      ])
    },
  })

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null

    setFile(null)
    setValidationError('')
    mutation.reset()

    if (!selected) return

    const extension = selected.name.split('.').pop()?.toLowerCase()

    if (!ALLOWED_EXTENSIONS.includes(extension ?? '')) {
      setValidationError('Selecciona un archivo PDF, PNG o JPG.')
      return
    }

    if (!selected.size || selected.size > MAX_FILE_SIZE) {
      setValidationError('El archivo debe tener contenido y no superar 4 MB.')
      return
    }

    setFile(selected)
  }

  function resetForm() {
    setFile(null)
    setValidationError('')
    mutation.reset()

    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }

  function startAnalysis() {
    if (file && !mutation.isPending) {
      mutation.mutate(file)
    }
  }

  return (
    <div className="space-y-7">
      <div>
        <p className="text-sm font-semibold text-teal-700">
          Inteligencia documental
        </p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">
          Analizar factura
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Extrae información y recibe observaciones automáticas
          mediante Azure Document Intelligence y GPT-5 mini.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">
          Seleccionar documento
        </h2>

        <div className="mt-5 rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <UploadCloud className="mx-auto text-teal-600" size={38} />

          <p className="mt-4 font-semibold text-slate-800">
            Selecciona una factura
          </p>
          <p className="mt-2 text-sm text-slate-500">
            Archivos PDF, PNG o JPG de hasta 4 MB
          </p>

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={selectFile}
            disabled={mutation.isPending}
            className="mt-5 block w-full text-sm text-slate-600 file:mr-4 file:rounded-lg file:border-0 file:bg-teal-600 file:px-4 file:py-2.5 file:font-semibold file:text-white hover:file:bg-teal-700"
            aria-label="Seleccionar factura"
          />
        </div>

        {file && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl bg-teal-50 p-4">
            <div className="flex min-w-0 items-center gap-3">
              <FileText className="shrink-0 text-teal-700" />
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-slate-900">
                  {file.name}
                </p>
                <p className="text-xs text-slate-500">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>

            <button
              type="button"
              disabled={mutation.isPending}
              onClick={resetForm}
              aria-label="Quitar archivo"
              className="rounded-lg p-2 text-slate-600 hover:bg-white disabled:opacity-50"
            >
              <X size={18} />
            </button>
          </div>
        )}

        {validationError && (
          <p role="alert" className="mt-4 text-sm text-red-700">
            {validationError}
          </p>
        )}

        <button
          type="button"
          onClick={startAnalysis}
          disabled={!file || mutation.isPending}
          className="mt-5 inline-flex items-center gap-2 rounded-xl bg-teal-600 px-6 py-3 text-sm font-bold text-white transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {mutation.isPending ? (
            <>
              <LoaderCircle className="animate-spin" size={18} />
              Procesando factura...
            </>
          ) : (
            <>
              <ScanLine size={18} />
              Iniciar análisis
            </>
          )}
        </button>

        <p className="mt-3 text-xs text-slate-500">
          El análisis comienza únicamente al presionar el botón.
          Puede consumir cuota de los servicios de Azure.
        </p>
      </section>

      {mutation.isPending && (
        <div
          role="status"
          className="flex items-center gap-3 rounded-2xl border border-teal-100 bg-teal-50 p-5"
        >
          <LoaderCircle className="animate-spin text-teal-700" size={22} />
          <p className="text-sm text-teal-900">
            Estamos extrayendo los datos, comprobando los importes
            y preparando las observaciones de la IA...
          </p>
        </div>
      )}

      {mutation.isError && (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-5">
          <div className="flex items-center gap-2 font-bold text-red-800">
            <AlertCircle size={19} />
            No fue posible completar el análisis
          </div>
          <p className="mt-2 text-sm text-red-700">
            {getErrorMessage(mutation.error)}
          </p>
          {axios.isAxiosError<{ related_invoice_id?: string }>(mutation.error) &&
            mutation.error.response?.status === 409 &&
            mutation.error.response.data?.related_invoice_id && (
              <Link
                to={`/facturas/${encodeURIComponent(mutation.error.response.data.related_invoice_id)}`}
                className="mt-2 inline-block text-sm font-semibold text-red-800 underline"
              >
                Ver factura relacionada
              </Link>
            )}
          <button
            type="button"
            onClick={() => mutation.reset()}
            className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-red-800"
          >
            <RefreshCw size={15} />
            Cerrar aviso
          </button>
        </div>
      )}

      {mutation.isSuccess && (
        <ResultPanel result={mutation.data} />
      )}
    </div>
  )
}
