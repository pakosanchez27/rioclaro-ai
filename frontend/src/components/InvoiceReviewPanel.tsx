import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'

import {
  AlertCircle,
  CheckCircle2,
  ClipboardCheck,
  History,
  XCircle,
} from 'lucide-react'

import {
  getInvoiceReviewHistory,
  reviewInvoice,
} from '../lib/api'
import type { ReviewDecision } from '../lib/api'

interface Props {
  invoiceId: string
  status: string
}

function errorMessage(error: Error): string {
  if (axios.isAxiosError<{ error?: string }>(error)) {
    const status = error.response?.status

    if (status === 409) {
      return 'Esta factura ya fue revisada. Actualiza la página.'
    }

    if (status === 400) {
      return error.response?.data?.error ?? 'Datos de revisión incorrectos.'
    }

    if (status === 401 || status === 403) {
      return 'No tienes autorización para realizar esta operación.'
    }
  }

  return 'No se pudo registrar la revisión.'
}

function formatReviewDate(value: string): string {
  const date = new Date(value)

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleString('es-MX', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
}

export default function InvoiceReviewPanel({
  invoiceId,
  status,
}: Props) {
  const queryClient = useQueryClient()

  const [decision, setDecision] = useState<ReviewDecision | null>(null)
  const [notes, setNotes] = useState('')

  const historyQuery = useQuery({
    queryKey: ['invoice-reviews', invoiceId],
    queryFn: () => getInvoiceReviewHistory(invoiceId),
  })

  const mutation = useMutation({
    mutationFn: (selectedDecision: ReviewDecision) =>
      reviewInvoice({
        invoice_id: invoiceId,
        decision: selectedDecision,
        notes: notes.trim(),
      }),
    retry: false,
    onSuccess: async () => {
      setDecision(null)
      setNotes('')

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['invoice', invoiceId],
        }),
        queryClient.invalidateQueries({
          queryKey: ['invoices'],
        }),
        queryClient.invalidateQueries({
          queryKey: ['invoice-stats'],
        }),
        queryClient.invalidateQueries({
          queryKey: ['invoice-reviews', invoiceId],
        }),
      ])
    },
  })

  const canReview = status === 'pending_review'

  function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!decision || mutation.isPending) return

    if (decision === 'reject' && !notes.trim()) return

    mutation.mutate(decision)
  }

  function chooseDecision(value: ReviewDecision) {
    setDecision(value)
    setNotes('')
    mutation.reset()
  }

  return (
    <section className="space-y-5">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <ClipboardCheck className="text-teal-700" size={22} />
          <h2 className="text-lg font-bold text-slate-900">
            Revisión de factura
          </h2>
        </div>

        {canReview ? (
          <>
            <p className="mt-3 text-sm text-slate-500">
              Revisa los datos y las observaciones antes de tomar una decisión.
              La operación quedará registrada en el historial.
            </p>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <button
                type="button"
                disabled={mutation.isPending}
                onClick={() => chooseDecision('approve')}
                className="flex items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-800 hover:bg-emerald-100 disabled:opacity-50"
              >
                <CheckCircle2 size={18} />
                Aprobar factura
              </button>

              <button
                type="button"
                disabled={mutation.isPending}
                onClick={() => chooseDecision('reject')}
                className="flex items-center justify-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-800 hover:bg-red-100 disabled:opacity-50"
              >
                <XCircle size={18} />
                Rechazar factura
              </button>
            </div>

            {decision && (
              <form
                onSubmit={submitReview}
                className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-5"
              >
                <h3 className="font-bold text-slate-900">
                  Confirmar {decision === 'approve' ? 'aprobación' : 'rechazo'}
                </h3>

                <p className="mt-2 text-sm text-slate-500">
                  {decision === 'approve'
                    ? 'Confirma que has comprobado la información del documento.'
                    : 'Indica por qué esta factura debe rechazarse.'}
                </p>

                <label
                  htmlFor="review-notes"
                  className="mt-4 block text-sm font-semibold text-slate-700"
                >
                  Observaciones {decision === 'reject' ? '(obligatorias)' : '(opcionales)'}
                </label>

                <textarea
                  id="review-notes"
                  rows={4}
                  maxLength={1000}
                  required={decision === 'reject'}
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  disabled={mutation.isPending}
                  placeholder="Describe el resultado de tu revisión..."
                  className="mt-2 w-full rounded-xl border border-slate-200 bg-white p-3 text-sm outline-none focus:border-teal-500"
                />

                <p className="mt-1 text-right text-xs text-slate-400">
                  {notes.length}/1000 caracteres
                </p>

                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    type="submit"
                    disabled={
                      mutation.isPending ||
                      (decision === 'reject' && !notes.trim())
                    }
                    className="rounded-xl bg-[#101C32] px-5 py-2.5 text-sm font-bold text-white disabled:opacity-50"
                  >
                    {mutation.isPending
                      ? 'Guardando revisión...'
                      : 'Confirmar decisión'}
                  </button>

                  <button
                    type="button"
                    disabled={mutation.isPending}
                    onClick={() => setDecision(null)}
                    className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            )}
          </>
        ) : (
          <p className="mt-3 text-sm text-slate-500">
            Esta factura ya no está pendiente de revisión. Su estado
            actual es <strong>{status}</strong>.
          </p>
        )}

        {mutation.isSuccess && (
          <div
            role="status"
            className="mt-4 rounded-xl bg-emerald-50 p-4 text-sm font-semibold text-emerald-800"
          >
            La decisión se registró correctamente.
          </div>
        )}

        {mutation.isError && (
          <div
            role="alert"
            className="mt-4 flex items-start gap-2 rounded-xl bg-red-50 p-4 text-sm text-red-700"
          >
            <AlertCircle size={18} className="shrink-0" />
            {errorMessage(mutation.error)}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <History className="text-slate-600" size={21} />
          <h2 className="text-lg font-bold text-slate-900">
            Historial de revisiones
          </h2>
        </div>

        {historyQuery.isPending ? (
          <p className="mt-4 text-sm text-slate-500">
            Cargando historial...
          </p>
        ) : historyQuery.isError ? (
          <p className="mt-4 text-sm text-red-700">
            No fue posible consultar el historial de auditoría.
          </p>
        ) : historyQuery.data.history.length === 0 ? (
          <p className="mt-4 text-sm text-slate-500">
            Todavía no se han registrado revisiones.
          </p>
        ) : (
          <ol className="mt-5 space-y-4">
            {historyQuery.data.history.map((review) => (
              <li
                key={review.id}
                className="border-l-2 border-teal-300 pl-4"
              >
                <p className="font-semibold text-slate-900">
                  {review.decision === 'approve'
                    ? 'Factura aprobada'
                    : 'Factura rechazada'}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {formatReviewDate(review.reviewed_at)}
                </p>

                <p className="mt-2 text-sm text-slate-700">
                  {review.notes || 'Sin observaciones adicionales'}
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  Responsable: {review.reviewed_by_oid}
                </p>
              </li>
            ))}
          </ol>
        )}

        <p className="mt-5 text-xs text-slate-400">
          En modo demo se registra el identificador ficticio del evaluador,
          no su identidad real.
        </p>
      </div>
    </section>
  )
}
