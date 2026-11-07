
import axios from 'axios'

export interface HealthResponse {
  status: string
  service: string
  version: string
  timestamp: string
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
if (import.meta.env.PROD && /^http:\/\//i.test(apiBaseUrl)) {
  throw new Error('La API publicada debe utilizar HTTPS')
}

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15000,
  headers: {
    Accept: 'application/json',
  },
})

export const evaluatorSession = {
  get token() { return sessionStorage.getItem('evaluator_token') },
  set(token: string, expiresAt: string) {
    sessionStorage.setItem('evaluator_token', token)
    sessionStorage.setItem('evaluator_expires_at', expiresAt)
  },
  clear() {
    sessionStorage.removeItem('evaluator_token')
    sessionStorage.removeItem('evaluator_expires_at')
  },
  get active() {
    const expires = sessionStorage.getItem('evaluator_expires_at')
    return Boolean(this.token && expires && Date.parse(expires) > Date.now())
  },
}

api.interceptors.request.use(config => {
  if (evaluatorSession.token) config.headers.Authorization = `Bearer ${evaluatorSession.token}`
  return config
})

api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401 && evaluatorSession.token) {
    evaluatorSession.clear()
    window.dispatchEvent(new Event('evaluator-session-expired'))
  }
  return Promise.reject(error)
})

export async function loginEvaluator(code: string) {
  const { data } = await api.post<{access_token: string, expires_at: string}>('/auth/evaluator/login', { code })
  evaluatorSession.set(data.access_token, data.expires_at)
}

export async function logoutEvaluator() {
  try { await api.post('/auth/evaluator/logout') }
  finally { evaluatorSession.clear() }
}

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
  duplicate_check?: {
    status: 'none' | 'confirmed' | 'possible' | 'not_evaluable'
    related_invoices: {
      invoice_id: string
      classification: 'confirmed' | 'possible'
      reason: string
    }[]
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

export interface SavedInvoiceAnalysis {
  invoice_id: string
  extraction: ExtractionResult
  analysis: InvoiceAnalysis
  created_at: string
}

export interface InvoiceAnalysisLookup {
  invoice_id: string
  data: SavedInvoiceAnalysis | null
}

export interface InvoiceReviewRecord {
  id: number
  invoice_id: string
  decision: 'approve' | 'reject'
  previous_status: string
  new_status: string
  notes: string | null
  reviewed_by_oid: string
  reviewed_at: string
}

export interface InvoiceReviewHistory {
  invoice_id: string
  history: InvoiceReviewRecord[]
  total: number
  limit: number
  offset: number
}

export type ReviewDecision = 'approve' | 'reject'

export interface ReviewInvoiceRequest {
  invoice_id: string
  decision: ReviewDecision
  notes: string
}

export interface ReviewInvoiceResponse {
  review_id: number
  invoice_id: string
  decision: ReviewDecision
  previous_status: string
  status: string
  notes: string
  reviewed_by: string
  reviewed_at: string
}

export async function getInvoiceAnalysis(
  invoiceId: string
): Promise<InvoiceAnalysisLookup> {
  const response = await api.get<InvoiceAnalysisLookup>(
    `/invoices/${encodeURIComponent(invoiceId)}/analysis`
  )

  return response.data
}

export async function getInvoiceReviewHistory(
  invoiceId: string
): Promise<InvoiceReviewHistory> {
  const response = await api.get<InvoiceReviewHistory>(
    `/invoices/${encodeURIComponent(invoiceId)}/reviews`
  )

  return response.data
}

export async function reviewInvoice(
  payload: ReviewInvoiceRequest
): Promise<ReviewInvoiceResponse> {
  const response = await api.post<ReviewInvoiceResponse>(
    '/invoices/review',
    payload
  )

  return response.data
}

export interface AssistantSource {
  kind: string
  id: string
  updated_at: string | null
}

export interface AssistantResponse {
  message_id: string
  conversation_id: string
  answer: string
  sources: AssistantSource[]
  information_type: string
  warnings: string[]
}

export async function askAssistant(
  message: string,
  conversationId: string | null
): Promise<AssistantResponse> {
  const { data } = await api.post<AssistantResponse>(
    '/assistant/ask',
    { message, conversation_id: conversationId },
    { timeout: 45_000 }
  )
  return data
}

export interface AssistantQuota {
  remaining: number
  limit: number
  resets_at: string
  timezone: 'UTC'
  enabled: boolean
  retry_after_seconds: number | null
}

export async function getAssistantQuota(): Promise<AssistantQuota> {
  const { data } = await api.get<AssistantQuota>('/assistant/quota')
  return data
}

export interface BusinessOptions {
  branches: { code: string; name: string }[]
  orders: { folio: string; branch_code: string }[]
}

export interface Complaint {
  folio: string
  order_folio: string
  branch_name: string
  message: string
  category: string
  status: string
  created_at: string
  updated_at: string
}

export interface BranchReport {
  branches: {
    code: string
    name: string
    delivered_sales: number
    pending_orders: number
    updated_at: string | null
  }[]
  products_sold: { sku: string; name: string; units_sold: number }[]
  currency: string
  data_label: string
}

export async function getBusinessOptions(): Promise<BusinessOptions> {
  const { data } = await api.get<BusinessOptions>('/business/options')
  return data
}

export async function getBranchReport(): Promise<BranchReport> {
  const { data } = await api.get<BranchReport>('/business/reports')
  return data
}

export async function createComplaint(payload: {
  order_folio: string
  branch_code: string
  category: string
  message: string
}): Promise<{ folio: string; status: string; created_at: string }> {
  const { data } = await api.post('/complaints', payload)
  return data
}

export async function getComplaint(folio: string): Promise<Complaint> {
  const { data } = await api.get<Complaint>(`/complaints/${encodeURIComponent(folio)}`)
  return data
}
