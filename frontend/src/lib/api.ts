
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

export interface ExtractionResult {
  supplier_name: string | null
  supplier_tax_id: string | null
  invoice_number: string | null
  invoice_date: string | null
  subtotal: number | null
  tax: number | null
  total: number | null
  currency: string | null
  confidence: Record<string, number | null>
  metadata: {
    model: string
    pages_analyzed: number
    limited_to_first_page: boolean
  }
}

export interface InvoiceFinding {
  type: string
  severity: 'info' | 'low' | 'medium' | 'high' | string
  field: string
  message: string
}

export interface InvoiceAnalysis {
  invoice_number: string | null
  financial_validation: {
    subtotal: number | null
    tax: number | null
    total: number | null
    currency: string | null
    is_consistent: boolean | null
    difference: string | null
  }
  findings: InvoiceFinding[]
  requires_human_review: boolean
  recommended_status: string
  ai_analysis: {
    summary: string
    review_steps: string[]
    deployment: string
  }
}

export interface AnalyzeInvoiceResponse {
  invoice_id: string
  status: string
  extraction: ExtractionResult
  analysis: InvoiceAnalysis
  created_at: string
}

export async function analyzeInvoice(
  file: File
): Promise<AnalyzeInvoiceResponse> {
  const extension = file.name.split('.').pop()?.toLowerCase()

  const mimeTypes: Record<string, string> = {
    pdf: 'application/pdf',
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
  }

  const contentType = mimeTypes[extension ?? '']

  if (!contentType) {
    throw new Error('Selecciona un archivo PDF, PNG o JPG.')
  }

  if (file.size === 0 || file.size > 4_000_000) {
    throw new Error(
      'El archivo debe tener contenido y no superar los 4 MB.'
    )
  }

  // Enviar el archivo directamente como bytes.
  // No utilizar FormData: el backend espera el cuerpo binario.
  const response = await api.post<AnalyzeInvoiceResponse>(
    '/invoices/analyze',
    file,
    {
      headers: {
        'Content-Type': contentType,
      },
      timeout: 180_000,
    }
  )

  return response.data
}
