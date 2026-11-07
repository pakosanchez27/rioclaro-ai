import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import FacturasPage from '../src/pages/FacturasPage'
import { getInvoices } from '../src/lib/api'
import type { Invoice } from '../src/lib/api'
import { renderPage } from './render'

vi.mock('../src/lib/api', () => ({ getInvoices: vi.fn() }))

const invoice: Invoice = {
  id: 'factura-003',
  supplier_name: 'Proveedor Demo C',
  supplier_tax_id: null,
  invoice_number: 'DEMO-003',
  invoice_date: '2026-11-03',
  currency: 'MXN',
  subtotal: 2000,
  tax: 320,
  total: 2320,
  status: 'pending_review',
  created_at: '2026-11-03T12:00:00Z',
  updated_at: '2026-11-03T12:00:00Z',
}

beforeEach(() => vi.resetAllMocks())

it('consulta la página y filtra solo los registros cargados', async () => {
  vi.mocked(getInvoices).mockResolvedValue([invoice])
  renderPage(<FacturasPage />)

  expect(screen.getByText('Cargando facturas...')).toBeInTheDocument()
  expect(await screen.findByText('DEMO-003')).toBeInTheDocument()
  expect(getInvoices).toHaveBeenCalledWith(20, 0)
  expect(screen.getByRole('link', { name: 'Ver detalle' })).toHaveAttribute('href', '/facturas/factura-003')

  fireEvent.change(screen.getByRole('textbox', { name: 'Buscar facturas' }), { target: { value: 'otro proveedor' } })
  expect(screen.getByText('No se encontraron facturas')).toBeInTheDocument()
})

it('muestra un error si la API falla', async () => {
  vi.mocked(getInvoices).mockRejectedValue(new Error('offline'))
  renderPage(<FacturasPage />)
  expect(await screen.findByText('No fue posible consultar las facturas')).toBeInTheDocument()
})
