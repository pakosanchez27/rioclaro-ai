import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ClipboardList, Search } from 'lucide-react'

import { createComplaint, getBusinessOptions, getComplaint } from '../lib/api'

export default function PedidosQuejasPage() {
  const options = useQuery({ queryKey: ['business-options'], queryFn: getBusinessOptions })
  const [orderFolio, setOrderFolio] = useState('')
  const [branchCode, setBranchCode] = useState('')
  const [category, setCategory] = useState('delivery')
  const [message, setMessage] = useState('')
  const [lookup, setLookup] = useState('')
  const [lookupFolio, setLookupFolio] = useState('')
  const create = useMutation({ mutationFn: createComplaint, retry: false })
  const complaint = useQuery({
    queryKey: ['complaint', lookupFolio],
    queryFn: () => getComplaint(lookupFolio),
    enabled: Boolean(lookupFolio),
    retry: false,
  })

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (create.isPending) return
    create.mutate({ order_folio: orderFolio, branch_code: branchCode, category, message })
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-teal-700">Atención al cliente</p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Pedidos y quejas</h1>
        <p className="mt-2 text-sm text-slate-600">Datos ficticios de demostración. No ingreses información personal real.</p>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2"><ClipboardList className="text-teal-700" /><h2 className="text-lg font-bold">Registrar queja</h2></div>
        {options.isPending ? <p className="mt-4 text-sm text-slate-500">Cargando pedidos y sucursales...</p> :
          options.isError ? <p role="alert" className="mt-4 text-sm text-red-700">No fue posible cargar las opciones. Recarga la página.</p> : (
            <form onSubmit={submit} className="mt-5 grid gap-4 sm:grid-cols-2">
              <label className="text-sm font-semibold text-slate-700">Pedido
                <select required value={orderFolio} onChange={(event) => {
                  const folio = event.target.value
                  setOrderFolio(folio)
                  setBranchCode(options.data.orders.find((order) => order.folio === folio)?.branch_code ?? '')
                }} className="mt-1 w-full rounded-xl border border-slate-200 p-3">
                  <option value="">Selecciona un pedido</option>
                  {options.data.orders.map((order) => <option key={order.folio} value={order.folio}>{order.folio}</option>)}
                </select>
              </label>
              <label className="text-sm font-semibold text-slate-700">Sucursal
                <select required value={branchCode} onChange={(event) => setBranchCode(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 p-3">
                  <option value="">Selecciona una sucursal</option>
                  {options.data.branches.map((branch) => <option key={branch.code} value={branch.code}>{branch.name}</option>)}
                </select>
              </label>
              <label className="text-sm font-semibold text-slate-700">Categoría
                <select value={category} onChange={(event) => setCategory(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 p-3">
                  <option value="delivery">Entrega</option><option value="product">Producto</option><option value="service">Servicio</option><option value="other">Otra</option>
                </select>
              </label>
              <label className="text-sm font-semibold text-slate-700 sm:col-span-2">Descripción del problema
                <textarea required minLength={10} maxLength={1000} value={message} onChange={(event) => setMessage(event.target.value)} rows={4}
                  className="mt-1 w-full rounded-xl border border-slate-200 p-3" placeholder="Describe un caso ficticio..." />
              </label>
              <button type="submit" disabled={create.isPending} className="rounded-xl bg-teal-600 px-5 py-3 font-semibold text-white disabled:opacity-50">
                {create.isPending ? 'Registrando...' : 'Registrar queja'}
              </button>
            </form>
          )}
        {create.isSuccess && <p role="status" className="mt-4 rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800">Queja registrada: <strong>{create.data.folio}</strong>. Estado: {create.data.status}.</p>}
        {create.isError && <p role="alert" className="mt-4 text-sm text-red-700">No fue posible registrar la queja. Verifica el pedido, la sucursal y la conexión.</p>}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2"><Search className="text-teal-700" /><h2 className="text-lg font-bold">Consultar folio</h2></div>
        <form onSubmit={(event) => { event.preventDefault(); setLookupFolio(lookup.trim()) }} className="mt-4 flex gap-2">
          <label htmlFor="complaint-folio" className="sr-only">Folio de queja</label>
          <input id="complaint-folio" value={lookup} onChange={(event) => setLookup(event.target.value)} placeholder="QUE-..." className="min-w-0 flex-1 rounded-xl border border-slate-200 p-3" />
          <button type="submit" disabled={!lookup.trim()} className="rounded-xl bg-[#101C32] px-4 py-3 font-semibold text-white disabled:opacity-50">Buscar</button>
        </form>
        {complaint.isPending && lookupFolio && <p className="mt-4 text-sm text-slate-500">Consultando...</p>}
        {complaint.isError && <p role="alert" className="mt-4 text-sm text-red-700">No se encontró el folio o la API no está disponible.</p>}
        {complaint.data && <div className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
          <p className="font-bold">{complaint.data.folio} · {complaint.data.status}</p>
          <p className="mt-1">Pedido {complaint.data.order_folio} · {complaint.data.branch_name}</p>
          <p className="mt-2">{complaint.data.message}</p>
        </div>}
      </section>
    </div>
  )
}
