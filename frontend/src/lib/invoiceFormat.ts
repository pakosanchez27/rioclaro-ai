export function formatMoney(
  amount: number,
  currency: string
): string {
  try {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
    }).format(amount)
  } catch {
    return `${amount.toFixed(2)} ${currency}`
  }
}

export function formatInvoiceDate(
  value: string | null
): string {
  if (!value) return 'Sin fecha'

  const date = new Date(`${value.slice(0, 10)}T12:00:00`)

  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('es-MX', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

export function statusLabel(status: string): string {
  switch (status) {
    case 'validated':
      return 'Validada'
    case 'pending_review':
      return 'Pendiente'
    case 'rejected':
      return 'Rechazada'
    default:
      return status
  }
}

export function statusClass(status: string): string {
  switch (status) {
    case 'validated':
      return 'bg-emerald-50 text-emerald-700'
    case 'pending_review':
      return 'bg-amber-50 text-amber-700'
    case 'rejected':
      return 'bg-red-50 text-red-700'
    default:
      return 'bg-slate-100 text-slate-700'
  }
}
