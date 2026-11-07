
import { Navigate, Route, Routes } from 'react-router-dom'

import AppLayout from './components/layout/AppLayout'
import DashboardPage from './pages/DashboardPage'
import PlaceholderPage from './pages/PlaceholderPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />

        <Route
          path="facturas"
          element={
            <PlaceholderPage
              title="Facturas"
              description="Consulta y administración de documentos."
            />
          }
        />

        <Route
          path="analizar"
          element={
            <PlaceholderPage
              title="Analizar factura"
              description="Carga y procesamiento inteligente de documentos."
            />
          }
        />

        <Route
          path="revisiones"
          element={
            <PlaceholderPage
              title="Revisiones"
              description="Aprobación y rechazo de facturas pendientes."
            />
          }
        />

        <Route
          path="historial"
          element={
            <PlaceholderPage
              title="Historial"
              description="Auditoría y trazabilidad de las revisiones."
            />
          }
        />

        <Route
          path="configuracion"
          element={
            <PlaceholderPage
              title="Configuración"
              description="Perfil y preferencias del sistema."
            />
          }
        />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
