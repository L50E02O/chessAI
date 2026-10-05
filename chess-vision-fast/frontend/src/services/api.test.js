import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { bestMove, clearContext, detectAndMove, getEngine } from './api'

function okJson(body) {
  return Promise.resolve({ ok: true, json: () => Promise.resolve(body), text: () => Promise.resolve('') })
}

describe('api client', () => {
  beforeEach(() => {
    global.fetch = vi.fn(() => okJson({ ok: 1 }))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('bestMove posts the FEN, turn and depth as JSON', async () => {
    await bestMove('fen-here', undefined, 'b', 20)
    const [url, options] = global.fetch.mock.calls[0]
    expect(url).toBe('http://localhost:8000/api/best_move')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ fen: 'fen-here', turn: 'b', depth: 20 })
  })

  it('detectAndMove sends the file and only non-empty query params', async () => {
    const file = new File(['x'], 'board.png', { type: 'image/png' })
    await detectAndMove(file, undefined, 'auto', null, 15)
    const [url, options] = global.fetch.mock.calls[0]
    const parsed = new URL(url)
    expect(parsed.pathname).toBe('/api/detect_and_move')
    expect(parsed.searchParams.get('orientation')).toBe('auto')
    expect(parsed.searchParams.get('depth')).toBe('15')
    expect(parsed.searchParams.has('turn')).toBe(false)
    expect(options.body.get('file')).toBeInstanceOf(File)
  })

  it('getEngine fetches engine info', async () => {
    global.fetch = vi.fn(() => okJson({ name: 'Stockfish 17', depth: 15 }))
    await expect(getEngine()).resolves.toEqual({ name: 'Stockfish 17', depth: 15 })
    expect(global.fetch.mock.calls[0][0]).toBe('http://localhost:8000/api/engine')
  })

  it('rejects with the response body when the request fails', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: false, text: () => Promise.resolve('boom') })
    )
    await expect(clearContext()).rejects.toThrow('boom')
  })
})
