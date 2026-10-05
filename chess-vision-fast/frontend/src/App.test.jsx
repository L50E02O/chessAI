import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import App from './App'
import { bestMove, getEngine, clearContext } from './services/api'
import { START_FEN } from './lib/chess'

vi.mock('./services/api')

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getEngine.mockResolvedValue({ name: 'TestEngine 1.0', depth: 20 })
    bestMove.mockResolvedValue({
      uci: 'e2e4',
      san: 'e4',
      score_text: '+0.50',
      lines: [{ rank: 1, move: 'e4', depth: 15, nps: '1M nps', continuation: 'e4' }]
    })
    clearContext.mockResolvedValue({ ok: true })
  })

  it('renders start position and engine name', async () => {
    render(<App />)
    expect(screen.getByText(/Ready/i)).toBeInTheDocument()
    
    await waitFor(() => {
      expect(screen.getByText(/TestEngine 1.0/i)).toBeInTheDocument()
    })
  })

  it('importing a PGN enables Previous move', async () => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: /import fen \/ pgn/i }))
    const textarea = screen.getByLabelText(/fen \/ pgn/i)
    fireEvent.change(textarea, { target: { value: '1. e4 e5 2. Nf3 Nc6' } })
    fireEvent.click(screen.getByRole('button', { name: /load position/i }))

    expect(await screen.findByText('e4')).toBeInTheDocument()
    expect(screen.getByText('Nc6')).toBeInTheDocument()

    const prevBtn = screen.getByTitle('Previous move')
    expect(prevBtn).not.toBeDisabled()
  })

  it('clicking Analyze shows returned best move', async () => {
    render(<App />)
    const analyzeBtn = screen.getByRole('button', { name: /analyze/i })
    fireEvent.click(analyzeBtn)

    await waitFor(() => {
      expect(bestMove).toHaveBeenCalled()
    })
    
    expect(await screen.findByText('1. e4')).toBeInTheDocument()
  })
})
