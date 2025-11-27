
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function _jsonResponse(response) {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Error en la API')
  }
  return response.json()
}

export function detectImage(file) {
  const form = new FormData()
  form.set('file', file)
  return fetch(`${API_BASE}/api/detect`, {
    method: 'POST',
    body: form,
  }).then(_jsonResponse)
}

export function detectAndMove(file) {
  const form = new FormData()
  form.set('file', file)
  return fetch(`${API_BASE}/api/detect_and_move`, {
    method: 'POST',
    body: form,
  }).then(_jsonResponse)
}

export function bestMove(fen, options = {}) {
  return fetch(`${API_BASE}/api/best_move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fen, options }),
  }).then(_jsonResponse)
}

export function openStream(onMessage, onError) {
  const socket = new WebSocket(`${API_BASE.replace(/^http/, 'ws')}/ws/stream`)
  socket.addEventListener('message', (event) => {
    try {
      onMessage(JSON.parse(event.data))
    } catch (error) {
      console.error(error)
    }
  })
  socket.addEventListener('error', onError)
  return {
    sendFrame(frameBase64) {
      socket.send(JSON.stringify({ frame: frameBase64 }))
    },
    close: () => socket.close(),
  }
}
