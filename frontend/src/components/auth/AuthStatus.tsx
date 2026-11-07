import { useState } from 'react'
import {
  useIsAuthenticated,
  useMsal,
} from '@azure/msal-react'
import { InteractionStatus } from '@azure/msal-browser'

import { loginRequest } from '../../auth/msalConfig'

export default function AuthStatus() {
  const { instance, accounts, inProgress } = useMsal()
  const authenticated = useIsAuthenticated()
  const [error, setError] = useState('')

  const busy = inProgress !== InteractionStatus.None

  async function signIn() {
    setError('')
    try {
      await instance.loginRedirect(loginRequest)
    } catch {
      setError('No fue posible iniciar sesión.')
    }
  }

  async function signOut() {
    setError('')
    try {
      await instance.logoutRedirect()
    } catch {
      setError('No fue posible cerrar sesión.')
    }
  }

  return (
    <div className="flex items-center gap-3">
      {authenticated ? (
        <>
          <span className="hidden text-sm text-slate-600 sm:block">
            {accounts[0]?.name || accounts[0]?.username}
          </span>

          <button
            onClick={signOut}
            disabled={busy}
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
          >
            Cerrar sesión
          </button>
        </>
      ) : (
        <button
          onClick={signIn}
          disabled={busy}
          className="rounded-xl bg-teal-500 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-600 disabled:opacity-50"
        >
          {busy ? 'Procesando...' : 'Iniciar sesión'}
        </button>
      )}

      {error && (
        <span role="alert" className="text-xs text-red-600">
          {error}
        </span>
      )}
    </div>
  )
}