
import { useState } from 'react'
import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import {
  InteractionRequiredAuthError,
  InteractionStatus,
} from '@azure/msal-browser'
import axios from 'axios'

import { getMyIdentity } from '../../lib/api'
import type { ApiIdentity } from '../../lib/api'

export default function ApiIdentityCheck() {
  const { instance, accounts, inProgress } = useMsal()
  const authenticated = useIsAuthenticated()

  const [identity, setIdentity] = useState<ApiIdentity | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const scope = import.meta.env.VITE_ENTRA_API_SCOPE as
    | string
    | undefined

  async function verifyIdentity() {
    setError('')
    setIdentity(null)

    const account = instance.getActiveAccount() ?? accounts[0]

    if (!account || !scope) {
      setError('Falta iniciar sesión o configurar el scope.')
      return
    }

    setLoading(true)

    try {
      const result = await instance.acquireTokenSilent({
        scopes: [scope],
        account,
      })

      const user = await getMyIdentity(result.accessToken)
      setIdentity(user)
    } catch (err) {
      if (err instanceof InteractionRequiredAuthError) {
        try {
          await instance.acquireTokenRedirect({
            scopes: [scope],
            account,
          })
          return
        } catch {
          setError(
            'Microsoft Entra no permitió solicitar el token. ' +
            'Comprueba el consentimiento administrativo.'
          )
        }
      } else if (axios.isAxiosError(err)) {
        const status = err.response?.status

        setError(
          status === 401
            ? 'HTTP 401: el backend rechazó el token.'
            : status === 403
              ? 'HTTP 403: el usuario no tiene los permisos requeridos.'
              : 'No fue posible conectar con la API.'
        )
      } else {
        setError(
          'No se pudo obtener el token de la API. ' +
          'Revisa los permisos de Microsoft Entra.'
        )
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-bold text-slate-900">
        Verificación de identidad
      </h2>

      <p className="mt-2 text-sm text-slate-500">
        Comprueba tu acceso a la API protegida de Río Claro AI.
      </p>

      {!authenticated ? (
        <p className="mt-4 text-sm text-amber-700">
          Primero inicia sesión con Microsoft.
        </p>
      ) : (
        <button
          onClick={verifyIdentity}
          disabled={
            loading ||
            inProgress !== InteractionStatus.None
          }
          className="mt-5 rounded-xl bg-teal-600 px-5 py-3 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50"
        >
          {loading ? 'Verificando...' : 'Verificar acceso a la API'}
        </button>
      )}

      {identity && (
        <div className="mt-5 rounded-xl bg-emerald-50 p-4 text-sm">
          <p className="font-bold text-emerald-800">
            Identidad verificada correctamente
          </p>
          <p className="mt-2 text-slate-700">
            Usuario: {identity.username}
          </p>
          <p className="mt-1 text-slate-700">
            Roles: {identity.roles.join(', ') || 'Sin roles'}
          </p>
        </div>
      )}

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </p>
      )}
    </section>
  )
}
