
import axios from 'axios'

export interface HealthResponse {
  status: string
  service: string
  version: string
  timestamp: string
}

export const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    Accept: 'application/json',
  },
})

export async function getHealth(): Promise<HealthResponse> {
  const response = await api.get<HealthResponse>('/health')
  return response.data
}

export interface ApiIdentity {
  user_id: string
  tenant_id: string
  username: string
  roles: string[]
}

export async function getMyIdentity(
  accessToken: string
): Promise<ApiIdentity> {
  const response = await api.get<ApiIdentity>('/auth/me', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  })

  return response.data
}

export interface Invoice {
  id: string
  supplier_name: string
  supplier_tax_id: string | null
  invoice_number: string | null
  invoice_date: string | null
  currency: string
  subtotal: number
  tax: number
  total: number
  status: string
  created_at: string
  updated_at: string
}

export interface InvoiceStats {
  total_invoices: number
  validated: number
  pending_review: number
  total_amount: number
}

export async function getInvoices(
  limit = 20,
  offset = 0
): Promise<Invoice[]> {
  const { data } = await api.get<{ data: Invoice[] }>(
    '/invoices',
    { params: { limit, offset } }
  )

  return data.data
}

export async function getInvoice(
  invoiceId: string
): Promise<Invoice> {
  const { data } = await api.get<Invoice>(
    `/invoices/${encodeURIComponent(invoiceId)}`
  )

  return data
}

export async function getInvoiceStats(): Promise<InvoiceStats> {
  const { data } = await api.get<InvoiceStats>(
    '/invoices/stats'
  )

  return data
}
