import { describe, expect, it } from 'vitest'
import { formatInvoiceDate, formatMoney, statusLabel } from '../src/lib/invoiceFormat'

describe('formato de facturas', () => {
  it('muestra ausencia de fecha sin inventarla', () => {
    expect(formatInvoiceDate(null)).toBe('Sin fecha')
  })

  it('conserva una fecha inválida para revisión', () => {
    expect(formatInvoiceDate('texto inválido')).toBe('texto inválido')
  })

  it('etiqueta el estado de revisión', () => {
    expect(statusLabel('pending_review')).toBe('Pendiente')
    expect(formatMoney(116, 'MXN')).toContain('116.00')
  })
})
