import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { BrainCircuit, Send, RotateCcw, AlertCircle, MicOff } from 'lucide-react'

import { askAssistant, getAssistantQuota } from '../lib/api'
import type { AssistantResponse } from '../lib/api'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  text: string
  result?: AssistantResponse
}

const suggestions = [
  '¿Cuánto cloro de un litro tenemos en León?',
  '¿Cuál es el estado del pedido PED-001?',
  '¿Cuál es la política vigente de devoluciones?',
  '¿Qué productos tienen existencias bajas?',
]

export default function AsistentePage() {
  const queryClient = useQueryClient()
  const quota = useQuery({ queryKey: ['assistant-quota'], queryFn: getAssistantQuota })
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: (message: string) => askAssistant(message, conversationId),
    retry: false,
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ['assistant-quota'] })
      setConversationId(result.conversation_id)
      setMessages((current) => [...current, {
        id: result.message_id,
        role: 'assistant',
        text: result.answer,
        result,
      }])
    },
    onError: () => {
      void queryClient.invalidateQueries({ queryKey: ['assistant-quota'] })
    },
  })

  function send(message: string) {
    const question = message.trim()
    if (!question || question.length > 500 || mutation.isPending || quota.data?.remaining === 0) return
    setMessages((current) => [...current, {
      id: crypto.randomUUID(), role: 'user', text: question,
    }])
    setDraft('')
    mutation.mutate(question)
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    send(draft)
  }

  function newConversation() {
    if (mutation.isPending) return
    setMessages([])
    setConversationId(null)
    setDraft('')
    mutation.reset()
  }

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-teal-700">Información empresarial</p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">Asistente Río Claro</h1>
          <p className="mt-2 text-sm text-slate-600">
            La IA selecciona consultas; las respuestas usan datos ficticios verificados del sistema.
          </p>
        </div>
        <button type="button" onClick={newConversation} disabled={mutation.isPending}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50">
          <RotateCcw size={16} /> Nueva conversación
        </button>
      </div>

      <div className="rounded-xl border border-teal-100 bg-teal-50 px-4 py-3 text-sm text-teal-900" aria-live="polite">
        {quota.isPending ? 'Consultando cuota diaria...' : quota.isError
          ? 'No fue posible consultar la cuota. Intenta actualizar la página.'
          : quota.data.enabled
            ? `${quota.data.remaining} de ${quota.data.limit} consultas disponibles. Reinicio: ${new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'America/Mexico_City' }).format(new Date(quota.data.resets_at))} (hora del centro de México).`
            : 'El asistente está suspendido temporalmente.'}
      </div>

      <div aria-live="polite" className="min-h-80 space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        {messages.length === 0 && (
          <div>
            <BrainCircuit className="text-teal-700" size={30} />
            <h2 className="mt-3 font-bold text-slate-900">¿Qué necesitas consultar?</h2>
            <p className="mt-1 text-sm text-slate-500">Productos, existencias, pedidos y políticas vigentes.</p>
            <div className="mt-5 grid gap-2 sm:grid-cols-2">
              {suggestions.map((question) => (
                <button key={question} type="button" onClick={() => send(question)} disabled={mutation.isPending || quota.data?.remaining === 0}
                  className="rounded-xl border border-teal-100 bg-teal-50 p-3 text-left text-sm text-teal-900 hover:bg-teal-100 disabled:opacity-50">
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={message.role === 'user' ? 'ml-auto max-w-xl rounded-2xl bg-[#101C32] p-4 text-sm text-white' : 'max-w-2xl rounded-2xl bg-slate-50 p-4 text-sm text-slate-800'}>
            <p className="whitespace-pre-wrap">{message.text}</p>
            {message.result && (
              <div className="mt-3 border-t border-slate-200 pt-3 text-xs text-slate-600">
                <p className="font-semibold">Fuentes consultadas</p>
                {message.result.sources.length ? (
                  <ul className="mt-1 space-y-1">
                    {message.result.sources.map((source) => (
                      <li key={`${source.kind}:${source.id}`}>{source.kind}: {source.id}{source.updated_at ? ` · Actualizado ${source.updated_at}` : ''}</li>
                    ))}
                  </ul>
                ) : <p className="mt-1">No se encontraron fuentes verificables.</p>}
                {message.result.warnings.map((warning) => <p key={warning} className="mt-2 text-amber-700">{warning}</p>)}
              </div>
            )}
          </div>
        ))}

        {mutation.isPending && <p role="status" className="text-sm text-teal-700">Consultando fuentes...</p>}
        {mutation.isError && (
          <div role="alert" className="flex items-start gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-700">
            <AlertCircle size={18} className="shrink-0" />
            {axios.isAxiosError<{ error?: string }>(mutation.error) && mutation.error.response?.status === 429
              ? mutation.error.response.data.error ?? 'Cuota diaria agotada. Consulta la fecha de reinicio.'
              : axios.isAxiosError(mutation.error) && mutation.error.response?.status === 503
                ? 'El servicio de IA está temporalmente suspendido.'
              : 'No fue posible consultar el asistente. Revisa la conexi?n o vuelve a intentarlo.'}
          </div>
        )}
      </div>

      <form onSubmit={submit} className="flex gap-2">
        <label htmlFor="assistant-question" className="sr-only">Pregunta para el asistente</label>
        <input id="assistant-question" value={draft} onChange={(event) => setDraft(event.target.value)}
          maxLength={500} placeholder="Escribe una pregunta..." disabled={mutation.isPending}
          className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-teal-500" />
        <button type="button" disabled title="Voz no disponible: Azure AI Speech no está configurado"
          aria-label="Voz no disponible: Azure AI Speech no está configurado"
          className="rounded-xl border border-slate-200 bg-white px-3 text-slate-400">
          <MicOff size={18} />
        </button>
        <button type="submit" disabled={!draft.trim() || mutation.isPending || quota.data?.remaining === 0}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-3 font-semibold text-white disabled:opacity-50">
          <Send size={18} /><span className="hidden sm:inline">Enviar</span>
        </button>
      </form>
    </div>
  )
}
