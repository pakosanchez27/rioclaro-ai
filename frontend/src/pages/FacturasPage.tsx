import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  FileText,
  Search,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  ArrowRight,
} from 'lucide-react'

import { getInvoices } from '../lib/api'
import {
  formatMoney,
  formatInvoiceDate,
  statusClass,
  statusLabel,
} from '../lib/invoiceFormat'

const PAGE_SIZE = 20

export default function FacturasPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')

  const { data, isPending, isError, isFetching, refetch } =
    useQuery({
      queryKey: ['invoices', page],
      queryFn: () =>
        getInvoices(PAGE_SIZE, (page - 1) * PAGE_SIZE),
    })

  // Los filtros se aplican solo a la pagina cargada.
  // Mas adelante implementaremos filtros globales
  // directamente desde el backend.
  const filtered = (data ?? []).filter((invoice) => {
    const query = search.toLowerCase().trim()

    const matchesSearch =
      !query ||
      (invoice.supplier_name ?? '')
        .toLowerCase()
        .includes(query) ||
      (invoice.invoice_number ?? '')
        .toLowerCase()
        .includes(query)

    const matchesStatus =
      status === 'all' || invoice.status === status

    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-teal-700">
            Gestión documental
          </p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">
            Facturas
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Consulta los documentos registrados en Río Claro AI.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void refetch()}
            disabled={isFetching}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 disabled:opacity-50"
          >
            <RefreshCw size={17} />
            Actualizar
          </button>

          <Link
            to="/analizar"
            className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
          >
            Analizar factura
            <ArrowRight size={17} />
          </Link>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="grid gap-3 border-b border-slate-100 p-5 md:grid-cols-[1fr_200px]">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-3 top-3 text-slate-400"
            />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Buscar proveedor o número..."
              aria-label="Buscar facturas"
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none focus:border-teal-500"
            />
          </div>

          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            aria-label="Filtrar estado"
            className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-teal-500"
          >
            <option value="all">Todos los estados</option>
            <option value="pending_review">Pendientes</option>
            <option value="validated">Validadas</option>
            <option value="rejected">Rechazadas</option>
          </select>
        </div>

        <p className="px-5 pt-3 text-xs text-slate-400">
          Búsqueda y filtros sobre la página actual.
        </p>

        {isPending ? (
          <div className="p-12 text-center text-slate-500">
            Cargando facturas...
          </div>
        ) : isError ? (
          <div className="p-12 text-center">
            <AlertCircle
              size={32}
              className="mx-auto text-red-500"
            />
            <p className="mt-3 font-semibold text-slate-800">
              No fue posible consultar las facturas
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Comprueba que la API esté disponible y que tengas acceso
              a las facturas de demostración.
            </p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center">
            <FileText
              size={36}
              className="mx-auto text-slate-300"
            />
            <p className="mt-3 font-semibold text-slate-800">
              No se encontraron facturas
            </p>
            <p className="mt-2 text-sm text-slate-500">
              Prueba con otros filtros o carga datos
              de demostración.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-180 text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-5 py-4">Factura</th>
                  <th className="px-5 py-4">Proveedor</th>
                  <th className="px-5 py-4">Fecha</th>
                  <th className="px-5 py-4">Importe</th>
                  <th className="px-5 py-4">Estado</th>
                  <th className="px-5 py-4">Acciones</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {filtered.map((invoice) => (
                  <tr
                    key={invoice.id}
                    className="hover:bg-slate-50/70"
                  >
                    <td className="px-5 py-4 font-semibold text-slate-900">
                      {invoice.invoice_number || 'Sin número'}
                    </td>

                    <td className="px-5 py-4 text-slate-600">
                      {invoice.supplier_name}
                    </td>

                    <td className="px-5 py-4 text-slate-500">
                      {formatInvoiceDate(invoice.invoice_date)}
                    </td>

                    <td className="px-5 py-4 font-semibold whitespace-nowrap text-slate-800">
                      {formatMoney(
                        invoice.total,
                        invoice.currency
                      )}
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold ${statusClass(invoice.status)}`}
                      >
                        {statusLabel(invoice.status)}
                      </span>
                    </td>

                    <td className="px-5 py-4">
                      <Link
                        to={`/facturas/${encodeURIComponent(invoice.id)}`}
                        className="font-semibold text-teal-700 hover:text-teal-900"
                      >
                        Ver detalle
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-5 py-4">
          <p className="text-xs text-slate-500">
            Página {page}
          </p>

          <div className="flex gap-2">
            <button
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page === 1 || isPending}
              className="rounded-lg border border-slate-200 p-2 text-slate-600 disabled:opacity-30"
              aria-label="Página anterior"
            >
              <ChevronLeft size={18} />
            </button>

            <button
              onClick={() => setPage((current) => current + 1)}
              disabled={
                isPending ||
                isError ||
                (data?.length ?? 0) < PAGE_SIZE
              }
              className="rounded-lg border border-slate-200 p-2 text-slate-600 disabled:opacity-30"
              aria-label="Página siguiente"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
