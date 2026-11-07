
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
