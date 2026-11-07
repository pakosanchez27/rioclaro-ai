import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import AnalizarFacturaPage from '../src/pages/AnalizarFacturaPage'
import { analyzeInvoice } from '../src/lib/api'
import type { AnalyzeInvoiceResponse } from '../src/lib/api'
import { renderPage } from './render'

vi.mock('../src/lib/api', () => ({ analyzeInvoice: vi.fn() }))

const result: AnalyzeInvoiceResponse = {
  invoice_id: 'factura-nueva',
  status: 'pending_review',
  created_at: '2026-11-07T12:00:00Z',
  extraction: {
    supplier_name: 'Proveedor Demo', supplier_tax_id: null,
    invoice_number: 'INV-1', invoice_date: '2026-11-07',
    subtotal: 100, tax: 16, total: 116, currency: 'MXN',
    confidence: {}, metadata: { model: 'prebuilt-invoice', pages_analyzed: 1, limited_to_first_page: true },
  },
  analysis: {
    invoice_number: 'INV-1',
    financial_validation: { subtotal: 100, tax: 16, total: 116, currency: 'MXN', is_consistent: true, difference: '0' },
    findings: [], requires_human_review: true, recommended_status: 'pending_review',
    ai_analysis: { summary: 'Revisión sugerida.', review_steps: [], deployment: 'gpt-rioclaro' },
  },
}

beforeEach(() => vi.resetAllMocks())

it('espera confirmación manual antes de enviar el archivo', async () => {
  vi.mocked(analyzeInvoice).mockResolvedValue(result)
  renderPage(<AnalizarFacturaPage />)

  const file = new File(['%PDF-1.4 ejemplo'], 'factura.pdf', { type: 'application/pdf' })
  fireEvent.change(screen.getByLabelText('Seleccionar factura'), { target: { files: [file] } })
  expect(analyzeInvoice).not.toHaveBeenCalled()

  fireEvent.click(screen.getByRole('button', { name: 'Iniciar análisis' }))
  expect(await screen.findByText('Análisis completado y guardado')).toBeInTheDocument()
  expect(vi.mocked(analyzeInvoice).mock.calls[0][0]).toBe(file)
  expect(screen.getByRole('link', { name: /Abrir factura guardada/ })).toHaveAttribute('href', '/facturas/factura-nueva')
})

it('rechaza un formato no admitido sin llamar la API', () => {
  renderPage(<AnalizarFacturaPage />)
  const file = new File(['texto'], 'factura.txt', { type: 'text/plain' })
  fireEvent.change(screen.getByLabelText('Seleccionar factura'), { target: { files: [file] } })
  expect(screen.getByRole('alert')).toHaveTextContent('Selecciona un archivo PDF, PNG o JPG.')
  expect(analyzeInvoice).not.toHaveBeenCalled()
})
