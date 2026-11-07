// Uso local: iniciar Chrome headless con --remote-debugging-port=9223.
import { writeFile } from 'node:fs/promises'

const url = process.argv[2] ?? 'http://127.0.0.1:5174/pedidos-quejas'
const output = process.argv[3] ?? '../docs/images/mobile-verified.png'
const tabs = await fetch('http://127.0.0.1:9223/json').then((response) => response.json())
const tab = tabs.find((item) => item.type === 'page')
if (!tab) throw new Error('Chrome no tiene una pestaña disponible')

const socket = new WebSocket(tab.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})

let nextId = 0
const pending = new Map()
socket.addEventListener('message', (event) => {
  const message = JSON.parse(event.data)
  const waiting = pending.get(message.id)
  if (!waiting) return
  pending.delete(message.id)
  if (message.error) waiting.reject(new Error(message.error.message))
  else waiting.resolve(message.result)
})

function call(method, params = {}) {
  const id = ++nextId
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject })
    socket.send(JSON.stringify({ id, method, params }))
  })
}

await call('Page.enable')
await call('Emulation.setDeviceMetricsOverride', {
  width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
})
await call('Page.navigate', { url })
await new Promise((resolve) => setTimeout(resolve, 3500))
const metrics = await call('Runtime.evaluate', {
  expression: '({ viewport: innerWidth, scrollWidth: document.documentElement.scrollWidth, title: document.title })',
  returnByValue: true,
})
const screenshot = await call('Page.captureScreenshot', {
  format: 'png', captureBeyondViewport: false,
})
await writeFile(output, Buffer.from(screenshot.data, 'base64'))
console.log(JSON.stringify(metrics.result.value))
socket.close()
