import { useQuery } from '@tanstack/react-query'
import { getBranchReport } from '../lib/api'
import { formatMoney } from '../lib/invoiceFormat'

export default function ReportesPage() {
  const { data, isPending, isError, refetch } = useQuery({ queryKey: ['branch-report'], queryFn: getBranchReport })
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-teal-700">Dirección general</p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Reportes de sucursales</h1>
        <p className="mt-2 text-sm text-slate-600">Ventas de pedidos entregados. Datos ficticios de demostración.</p>
      </div>
      {isPending ? <p className="rounded-2xl bg-white p-6 text-slate-500">Cargando reporte...</p> :
        isError ? <div className="rounded-2xl bg-white p-6 text-red-700">No fue posible cargar el reporte. <button onClick={() => void refetch()} className="underline">Reintentar</button></div> : (
          <>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              {data.branches.map((branch) => <div key={branch.code} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="font-bold text-slate-900">{branch.name}</h2>
                <p className="mt-3 text-lg font-bold text-teal-700">{formatMoney(branch.delivered_sales, data.currency)}</p>
                <p className="mt-2 text-sm text-slate-600">Pedidos pendientes: {branch.pending_orders}</p>
                <p className="mt-2 text-xs text-slate-400">Actualizado: {branch.updated_at ?? 'Sin pedidos'}</p>
              </div>)}
            </div>
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="font-bold text-slate-900">Productos vendidos</h2>
              {data.products_sold.length ? <ul className="mt-3 space-y-2 text-sm text-slate-700">
                {data.products_sold.map((product) => <li key={product.sku}>{product.name}: {product.units_sold} {product.units_sold === 1 ? 'unidad' : 'unidades'}</li>)}
              </ul> : <p className="mt-3 text-sm text-slate-500">Sin pedidos entregados.</p>}
            </section>
          </>
        )}
    </div>
  )
}
