const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function _jsonResponse(response) {
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || 'Error en la API')
  }
  return response.json()
}

export function detectImage(file, signal) {
  const form = new FormData()
  form.set('file', file)
  return fetch(`${API_BASE}/api/detect`, {
    method: 'POST',
    body: form,
    signal,
  }).then(_jsonResponse)
}

export function detectAndMove(file, signal, model) {
  const form = new FormData()
  form.set('file', file)
  const url = new URL(`${API_BASE}/api/detect_and_move`)
  if (model) {
    url.searchParams.set('model', model)
  }
  return fetch(url.toString(), {
    method: 'POST',
    body: form,
    signal,
  }).then(_jsonResponse)
}

export function bestMove(fen, signal, model) {
  return fetch(`${API_BASE}/api/best_move`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fen, model }),
    signal,
  }).then(_jsonResponse)
}

export function clearContext(signal) {
  return fetch(`${API_BASE}/api/clear_context`, {
    method: 'POST',
    signal,
  }).then(_jsonResponse)
}

export function getRetrospective(signal) {
  return fetch(`${API_BASE}/api/retrospective`, {
    method: 'GET',
    signal,
  }).then(_jsonResponse)
}

export function changeModel(model) {
  return fetch(`${API_BASE}/api/change_model`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  }).then(_jsonResponse)
}

export function getCurrentModel() {
  return fetch(`${API_BASE}/api/current_model`, {
    method: 'GET',
  }).then(_jsonResponse)
}
