const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function _jsonResponse(response) {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Error en la API')
  }
  return response.json()
}

function _query(url, params) {
  const u = new URL(url)
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== '') {
      u.searchParams.set(key, value)
    }
  }
  return u.toString()
}

export function detectImage(file, signal, orientation) {
  const form = new FormData()
  form.set('file', file)
  return fetch(_query(`${API_BASE}/api/detect`, { orientation }), {
    method: 'POST',
    body: form,
    signal,
  }).then(_jsonResponse)
}

export function detectAndMove(file, signal, orientation, turn, depth) {
  const form = new FormData()
  form.set('file', file)
  return fetch(_query(`${API_BASE}/api/detect_and_move`, { orientation, turn, depth }), {
    method: 'POST',
    body: form,
    signal,
  }).then(_jsonResponse)
}

export function bestMove(fen, signal, turn, depth) {
  return fetch(`${API_BASE}/api/best_move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fen, turn, depth }),
    signal,
  }).then(_jsonResponse)
}

export function clearContext(signal) {
  return fetch(`${API_BASE}/api/clear_context`, {
    method: 'POST',
    signal,
  }).then(_jsonResponse)
}

export function getContext(signal) {
  return fetch(`${API_BASE}/api/context`, {
    method: 'GET',
    signal,
  }).then(_jsonResponse)
}

export function getEngine(signal) {
  return fetch(`${API_BASE}/api/engine`, {
    method: 'GET',
    signal,
  }).then(_jsonResponse)
}
