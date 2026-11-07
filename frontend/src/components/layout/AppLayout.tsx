
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  ScanLine,
  ClipboardCheck,
  History,
  Settings,
  Menu,
  X,
  Sparkles,
  ShieldCheck,
} from 'lucide-react'

const navigation = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/facturas', label: 'Facturas', icon: FileText },
  { to: '/analizar', label: 'Analizar factura', icon: ScanLine },
  { to: '/revisiones', label: 'Revisiones', icon: ClipboardCheck },
  { to: '/historial', label: 'Historial', icon: History },
  { to: '/configuracion', label: 'Configuración', icon: Settings },
]

export default function AppLayout() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-[#F5F7FB] md:flex">
      {menuOpen && (
        <button
          className="fixed inset-0 z-40 bg-slate-950/50 md:hidden"
          aria-label="Cerrar menú"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-65
          flex-col bg-[#0B1220] text-white transition-transform
          duration-200 md:sticky md:top-0 md:h-screen
          md:translate-x-0
          ${menuOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-teal-400 text-slate-950">
              <Sparkles size={23} strokeWidth={2.4} />
            </div>
            <div>
              <p className="text-lg font-bold tracking-tight">
                Río Claro AI
              </p>
              <p className="text-xs text-slate-400">
                Gestión inteligente
              </p>
            </div>
          </div>

          <button
            className="md:hidden"
            aria-label="Cerrar navegación"
            onClick={() => setMenuOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-6">
          <p className="mb-4 px-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            Espacio de trabajo
          </p>

          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-4 py-3
                 text-sm font-medium transition-colors ${
                   isActive
                     ? 'bg-teal-400/15 text-teal-300'
                     : 'text-slate-400 hover:bg-white/5 hover:text-white'
                 }`
              }
            >
              <Icon size={19} strokeWidth={1.8} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 p-5">
          <div className="flex items-start gap-3 rounded-xl bg-white/5 p-3">
            <ShieldCheck className="mt-0.5 shrink-0 text-teal-300" size={19} />
            <div>
              <p className="text-xs font-semibold">
                Entorno de desarrollo
              </p>
              <p className="mt-1 text-xs leading-relaxed text-slate-400">
                La autenticación de usuarios se habilitará próximamente.
              </p>
            </div>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-30 flex h-18 items-center justify-between border-b border-slate-200 bg-white/95 px-5 backdrop-blur md:px-9">
          <div className="flex items-center gap-3">
            <button
              className="rounded-lg p-2 text-slate-700 hover:bg-slate-100 md:hidden"
              aria-label="Abrir navegación"
              onClick={() => setMenuOpen(true)}
            >
              <Menu size={22} />
            </button>
            <div>
              <p className="text-sm font-semibold text-slate-900">
                Panel de gestión
              </p>
              <p className="text-xs text-slate-500">
                Río Claro AI
              </p>
            </div>
          </div>

          <span className="inline-flex items-center gap-2 rounded-full bg-teal-50 px-4 py-2 text-xs font-semibold text-teal-700">
            Modo demostración
          </span>
        </header>

        <main className="mx-auto w-full max-w-350 px-5 py-8 md:px-9">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
