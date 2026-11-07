import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, FileText, AlertCircle } from 'lucide-react'
import axios from 'axios'

import { getInvoice } from '../lib/api'
import InvoiceAnalysisPanel from '../components/InvoiceAnalysisPanel'
import InvoiceReviewPanel from '../components/InvoiceReviewPanel'
import {
  formatMoney,
  formatInvoiceDate,
  statusClass,
  statusLabel,
} from '../lib/invoiceFormat'

export default function FacturaDetallePage() {
  const { factura_id = '' } = useParams()

  const { data: invoice, isPending, error } = useQuery({
    queryKey: ['invoice', factura_id],
    queryFn: () => getInvoice(factura_id),
    enabled: Boolean(factura_id),
  })

  return (
    <div className="space-y-6">
      <Link
        to="/facturas"
        className="inline-flex items-center gap-2 text-sm font-semibold text-teal-700"
      >
        <ArrowLeft size={17} />
        Volver a facturas
      </Link>

      {isPending ? (
        <div className="rounded-2xl bg-white p-10 text-center text-slate-500">
          Cargando detalle...
        </div>
      ) : error ? (
        <div className="rounded-2xl border border-red-100 bg-white p-10 text-center">
          <AlertCircle className="mx-auto text-red-500" />
          <p className="mt-3 font-semibold">
            {axios.isAxiosError(error) && error.response?.status === 404
              ? 'Factura no encontrada'
              : 'No fue posible cargar el detalle'}
          </p>
        </div>
      ) : invoice ? (
        <>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-teal-700">
                Detalle de factura
              </p>
              <h1 className="mt-1 text-3xl font-bold text-slate-900">
                {invoice.invoice_number || 'Sin número'}
              </h1>
              <p className="mt-2 text-sm text-slate-500">
                {invoice.supplier_name}
              </p>
            </div>

            <span
              className={`rounded-full px-4 py-2 text-sm font-semibold ${statusClass(invoice.status)}`}
            >
              {statusLabel(invoice.status)}
            </span>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
              <div className="flex items-center gap-3">
                <FileText size={22} className="text-teal-700" />
                <h2 className="text-lg font-bold text-slate-900">
                  Información del documento
                </h2>
              </div>

              <dl className="mt-6 grid gap-5 sm:grid-cols-2">
                {[
                  ['Proveedor', invoice.supplier_name],
                  ['Identificador fiscal', invoice.supplier_tax_id || 'No detectado'],
                  ['Número de factura', invoice.invoice_number || 'No detectado'],
                  ['Fecha de emisión', formatInvoiceDate(invoice.invoice_date)],
                  ['Moneda', invoice.currency],
                  ['ID interno', invoice.id],
                ].map(([label, value]) => (
                  <div key={label} className="min-w-0">
                    <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      {label}
                    </dt>
                    <dd className="mt-2 break-words text-sm font-semibold text-slate-800">
                      {value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900">
                Resumen financiero
              </h2>

              <dl className="mt-6 space-y-4">
                <div className="flex justify-between gap-2 text-sm">
                  <dt className="text-slate-500">Subtotal</dt>
                  <dd className="font-semibold">
                    {formatMoney(invoice.subtotal, invoice.currency)}
                  </dd>
                </div>

                <div className="flex justify-between gap-2 text-sm">
                  <dt className="text-slate-500">Impuestos</dt>
                  <dd className="font-semibold">
                    {formatMoney(invoice.tax, invoice.currency)}
                  </dd>
                </div>

                <div className="border-t border-slate-100 pt-4">
                  <dt className="text-sm text-slate-500">Total</dt>
                  <dd className="mt-2 break-words text-2xl font-bold text-teal-700">
                    {formatMoney(invoice.total, invoice.currency)}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          <InvoiceAnalysisPanel invoiceId={invoice.id} />

          <InvoiceReviewPanel
            invoiceId={invoice.id}
            status={invoice.status}
          />
        </>
      ) : null}
    </div>
  )
}
