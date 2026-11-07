
import { ArrowLeft, Construction } from 'lucide-react'
import { Link } from 'react-router-dom'

interface Props {
  title: string
  description: string
}

export default function PlaceholderPage({
  title,
  description,
}: Props) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">
          {title}
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          {description}
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white px-6 py-16 text-center shadow-sm">
        <div className="mx-auto flex size-16 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
          <Construction size={28} />
        </div>

        <h2 className="mt-5 text-xl font-bold text-slate-900">
          Módulo en construcción
        </h2>

        <p className="mx-auto mt-2 max-w-sm text-sm text-slate-500">
          Esta pantalla se implementará en las próximas
          etapas de Río Claro AI.
        </p>

        <Link
          to="/"
          className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#101C32] px-5 py-3 text-sm font-semibold text-white hover:bg-slate-700"
        >
          <ArrowLeft size={16} />
          Volver al dashboard
        </Link>
      </div>
    </div>
  )
}
