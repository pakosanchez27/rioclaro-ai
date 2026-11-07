# Río Claro AI

**Prototipo de inteligencia artificial para la Distribuidora Río Claro**  
Proyecto integrador AI-901 · Microsoft Azure AI Fundamentals · Demostración educativa

Río Claro AI es una aplicación web que reúne información comercial de una empresa ficticia dedicada a distribuir productos de limpieza e higiene. Su objetivo es mostrar cómo pasar de datos dispersos a herramientas útiles: extracción automática de facturas, prevención de duplicados, consultas de negocio mediante IA, seguimiento de pedidos, registro de quejas y reportes.

> **Uso académico y datos ficticios.** No introducir información personal, financiera o comercial real. Las respuestas de IA y los datos extraídos de facturas deben revisarse antes de tomar decisiones.

## 1. Acceso a la demostración

**Aplicación:** https://purple-rock-0f2728210.5.azurestaticapps.net/

**Código de acceso:** se comparte por un canal privado con los evaluadores autorizados; no está incluido en esta documentación pública.

### Cómo iniciar sesión

1. Abre la URL anterior en un navegador actualizado, desde computadora o celular.
2. En la pantalla de evaluación introduce el código de acceso exactamente como aparece arriba, respetando mayúsculas, minúsculas y guiones bajos.
3. Selecciona la opción de ingreso que aparezca en la pantalla.
4. Una vez dentro, utiliza el menú de la aplicación para recorrer los módulos.
5. Al terminar, utiliza **Cerrar sesión**.

La sesión temporal tiene una duración máxima de **2 horas**. Si expira, vuelve a iniciar sesión con el código de evaluación. El acceso depende de que el responsable del proyecto mantenga activado el periodo de evaluación.

## 2. ¿Qué problema resuelve?

La Distribuidora Río Claro tiene sucursales en **Guadalajara, Zapopan, León, Querétaro y Aguascalientes**. En el caso de estudio, sus facturas, productos, inventarios, pedidos, políticas y quejas se gestionan mediante fuentes dispersas. Esto dificulta encontrar información consistente y detectar errores.

El prototipo demuestra una alternativa con datos estructurados, controles de revisión humana e inteligencia artificial conectada a servicios de Azure.

## 3. Guía de módulos y funcionalidades

> Los nombres de las opciones pueden variar ligeramente según la versión desplegada. Los apartados de productos, inventarios y pedidos pueden consultarse a través del asistente, sin necesariamente constituir pantallas independientes.

### 3.1. Facturas y análisis inteligente

**Para qué sirve:** procesar facturas de proveedores, extraer sus datos y apoyar su validación antes de guardarlas.

**Qué se puede hacer:**

- Consultar las facturas registradas y sus detalles.
- Cargar una factura de prueba en **PDF** (el endpoint de análisis contempla un máximo de **4 MB**).
- Solicitar extracción automática de campos mediante **Azure AI Document Intelligence**.
- Revisar los datos obtenidos, como proveedor, fecha, importes y otros conceptos que estén presentes en el documento.
- Consultar advertencias de validación y posibles duplicados.
- Revisar o corregir datos mediante el flujo de revisión disponible y consultar su historial.

**Prueba sugerida:** utiliza una factura PDF ficticia, revisa los campos extraídos y comprueba si el sistema advierte sobre un posible registro duplicado al procesar una factura equivalente. No se debe asumir que toda advertencia implica un duplicado confirmado.

**Importante:** el documento no se considera correcto solamente porque la IA haya extraído información; una persona debe validar los datos.

### 3.2. Asistente inteligente

**Para qué sirve:** responder preguntas frecuentes de clientes y empleados utilizando los datos de demostración del negocio.

**Qué se puede hacer:**

- Consultar productos y disponibilidad registrada.
- Preguntar sobre inventario por sucursal.
- Solicitar información o seguimiento de pedidos registrados.
- Consultar las políticas de negocio incluidas en los datos de prueba.
- Obtener respuestas en lenguaje natural mediante **Azure OpenAI**.

**Preguntas sugeridas:**

- ¿Qué productos de limpieza aparecen en el catálogo?
- ¿Qué existencias hay en la sucursal de León?
- ¿Cómo puedo consultar el estado de un pedido?
- ¿Cuál es la política de devoluciones registrada?

Para consultas específicas de un pedido, utiliza un identificador existente en los datos de demostración. El asistente puede señalar información insuficiente cuando la pregunta no se puede verificar.

### 3.3. Consultas por voz

**Para qué sirve:** facilitar la interacción con el asistente sin escribir todas las preguntas.

**Cómo utilizarlo:** entra al área del asistente y utiliza el control de micrófono, si está disponible. Autoriza el acceso al micrófono cuando lo solicite el navegador, dicta una pregunta y revisa el texto reconocido y la respuesta.

La disponibilidad depende del dispositivo, del navegador y de sus permisos. Si falla el micrófono, escribe la misma pregunta para continuar la demostración.

### 3.4. Productos, inventario y pedidos

**Para qué sirve:** mostrar cómo la información comercial estructurada puede consultarse desde un punto central, evitando respuestas contradictorias entre sucursales.

**Qué se puede consultar:**

- Productos del catálogo y sus denominaciones.
- Existencias o disponibilidad registrada por sucursal.
- Pedidos y su estado dentro del conjunto de datos de prueba.
- Información comercial que el asistente pueda recuperar de las fuentes disponibles.

**Prueba sugerida:** pregunta por un mismo producto en dos sucursales distintas y compara las respuestas. Después consulta un pedido de demostración. Estos datos son ficticios y no representan inventario real.

### 3.5. Quejas y atención a clientes

**Para qué sirve:** centralizar reportes de clientes para que no se pierdan entre llamadas, mensajes y correos.

**Cómo usarlo:** entra al apartado de quejas, completa los campos visibles con información ficticia y registra un caso. Si la versión desplegada ofrece una vista de detalle, comprueba que el registro esté disponible.

**Prueba sugerida:** registra un reporte ficticio por retraso en una entrega y verifica que el sistema confirme su recepción. No utilices datos personales reales.

### 3.6. Reportes empresariales

**Para qué sirve:** consultar información de negocio de manera organizada para apoyar decisiones de operación.

**Cómo usarlo:** abre Reportes, selecciona los filtros u opciones que aparezcan y revisa los resultados. Contrasta los valores con los datos de ejemplo cuando sea posible.

**Prueba sugerida:** revisa los reportes disponibles y explica cómo una vista centralizada podría ayudar a comparar operaciones entre sucursales. Los datos y métricas pertenecen a un escenario de demostración.

## 4. Recorrido recomendado para evaluar el proyecto

1. **Acceso:** ingresar con el código de evaluación.
2. **Datos de negocio:** explorar las consultas de productos, existencias y pedidos.
3. **Asistente:** enviar una pregunta sobre productos o políticas.
4. **Voz:** repetir una pregunta mediante el micrófono, si el navegador lo permite.
5. **Facturas:** cargar un PDF ficticio, analizarlo, revisar resultados y consultar validaciones.
6. **Quejas:** registrar un caso de prueba.
7. **Reportes:** consultar los resultados disponibles.
8. **Cierre:** cerrar sesión y verificar que las pantallas protegidas vuelvan a requerir acceso.

## 5. Límites de uso de inteligencia artificial

La demostración utiliza cuotas del lado del servidor:

| Operación | Límite de producción configurado |
| --- | ---: |
| Preguntas al asistente | 20 por día |
| Análisis inteligentes de facturas | 5 por día |

Las cuotas se comparten en el entorno de demostración y se reinician por periodos definidos con referencia a **00:00 UTC**. Pueden agotarse si otras personas ya utilizaron el sistema. La IA también puede estar suspendida temporalmente por el responsable de la prueba.

**Mensajes habituales:**

| Situación | Qué significa / qué hacer |
| --- | --- |
| Código incorrecto | Verificar que esté escrito exactamente como se proporcionó. |
| Sesión expirada | Volver a iniciar sesión. |
| `401 Unauthorized` | La solicitud carece de una sesión válida. |
| `429 Too Many Requests` | Se alcanzó un límite; no repetir llamadas indiscriminadamente. |
| Servicio de IA suspendido / `503` | El responsable deshabilitó temporalmente una operación de IA. |
| Archivo rechazado | Comprobar que sea un PDF válido y que no exceda 4 MB. |
| No funciona el micrófono | Revisar permisos y compatibilidad del navegador. |

## 6. Arquitectura de la demostración

| Componente | Tecnología | Función |
| --- | --- | --- |
| Aplicación web | React, TypeScript, Vite | Interfaz accesible desde computadora y móvil. |
| Publicación del frontend | Azure Static Web Apps | Alojamiento HTTPS de React. |
| API | Python y Azure Functions | Lógica de negocio y endpoints protegidos. |
| Datos | Azure Table Storage | Persistencia de los registros y datos del prototipo. |
| IA generativa | Azure OpenAI, despliegue `gpt-rioclaro` | Respuestas del asistente y tareas de IA compatibles con el modelo. |
| Procesamiento documental | Azure AI Document Intelligence | Extracción de información de facturas. |
| Observabilidad | Application Insights | Telemetría técnica del backend. |

**API de estado:** https://func-rioclaro-626839.azurewebsites.net/api/health

El entorno de demostración utiliza registros ficticios. En una migración inicial se incorporaron **46 entidades** a Azure Tables; esta cifra puede cambiar cuando se utilizan los módulos.

## 7. Inteligencia artificial responsable

El prototipo considera los seis principios de IA responsable de Microsoft:

1. **Equidad:** evitar inferencias discriminatorias y utilizar datos pertinentes.
2. **Confiabilidad y seguridad:** validar entradas y resultados; no confiar ciegamente en la extracción de documentos.
3. **Privacidad y seguridad:** proteger el acceso a los datos y no incluir información real en las pruebas.
4. **Inclusión:** ofrecer interacción escrita y, donde esté disponible, por voz.
5. **Transparencia:** indicar cuándo interviene IA y distinguir datos extraídos de información validada.
6. **Responsabilidad:** mantener la revisión y las decisiones importantes bajo control humano.

Estos son criterios de diseño y evaluación; no constituyen una certificación de cumplimiento ni sustituyen auditorías de seguridad.

## 8. Alcance y limitaciones

- Es un **prototipo académico**, no un sistema comercial ni contable listo para producción.
- Se deben utilizar **facturas y datos ficticios**.
- El asistente depende de las fuentes disponibles y puede equivocarse o responder que no encuentra información.
- La calidad de extracción de las facturas varía según el contenido y la legibilidad del PDF.
- Las funciones de IA pueden estar desactivadas o sujetas a cuotas y disponibilidad de los servicios Azure.
- El acceso del evaluador es temporal y puede ser desactivado por el responsable del proyecto.

## 9. Información para el responsable técnico

**Grupo de recursos:** `rg-rioclaro-ai-dev`  
**Function App:** `func-rioclaro-626839`  
**Static Web App:** `swa-rioclaro-626839`  
**Storage:** `strioclaro626839`  
**Tabla de datos:** `RioClaroDemo`

Documentación de configuración y publicación: `docs/EVALUACION_SEGURA.md`, `docs/DESPLIEGUE_AZURE.md` y `docs/ALMACENAMIENTO_AZURE.md` (según los archivos presentes en el repositorio).

Para cerrar el acceso y detener llamadas nuevas a IA:

```powershell
az functionapp config appsettings set `
  -g 'rg-rioclaro-ai-dev' `
  -n 'func-rioclaro-626839' `
  --settings 'EVALUATOR_ACCESS_ENABLED=false' 'ENABLE_ASSISTANT=false' 'ENABLE_INVOICE_ANALYSIS=false' `
  --output none
```

No incorporar claves de Azure OpenAI, Document Intelligence, tokens de sesión ni archivos `.env` al repositorio. **No publiques códigos de evaluación ni otro material confidencial.**

---

**Río Claro AI** · Prototipo educativo para el proyecto integrador AI-901.
