import { beforeEach, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import AsistentePage from '../src/pages/AsistentePage'
import { askAssistant, getAssistantQuota } from '../src/lib/api'
import { renderPage } from './render'

vi.mock('../src/lib/api', () => ({ askAssistant: vi.fn(), getAssistantQuota: vi.fn() }))

beforeEach(() => vi.resetAllMocks())

it('muestra respuesta y fuente verificable', async () => {
  vi.mocked(getAssistantQuota).mockResolvedValue({ remaining: 99, limit: 100, resets_at: '2026-11-08T00:00:00Z', timezone: 'UTC', enabled: true, retry_after_seconds: null })
  vi.mocked(askAssistant).mockResolvedValue({
    message_id: 'm-1', conversation_id: 'c-1',
    answer: 'León: 42 piezas de cloro.',
    information_type: 'inventory', warnings: ['Datos ficticios de demostración'],
    sources: [{ kind: 'inventory', id: 'LIM-001:leo', updated_at: '2026-11-07T12:00:00Z' }],
  })
  renderPage(<AsistentePage />)

  expect(await screen.findByText(/99 de 100 consultas disponibles/)).toBeInTheDocument()

  fireEvent.change(screen.getByLabelText('Pregunta para el asistente'), { target: { value: '¿Cuánto cloro hay en León?' } })
  fireEvent.click(screen.getByRole('button', { name: 'Enviar' }))

  expect(await screen.findByText('León: 42 piezas de cloro.')).toBeInTheDocument()
  expect(screen.getByText(/inventory: LIM-001:leo/)).toBeInTheDocument()
  expect(askAssistant).toHaveBeenCalledWith('¿Cuánto cloro hay en León?', null)
})
