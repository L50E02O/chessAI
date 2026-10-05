import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import ImportModal from './ImportModal'

function setup() {
  const onImport = vi.fn()
  const onClose = vi.fn()
  render(<ImportModal isOpen onClose={onClose} onImport={onImport} />)
  const textarea = screen.getByLabelText(/fen \/ pgn/i)
  const load = screen.getByRole('button', { name: /load position/i })
  return { onImport, onClose, textarea, load }
}

describe('ImportModal', () => {
  it('renders nothing when closed', () => {
    const { container } = render(<ImportModal isOpen={false} onClose={() => {}} onImport={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('imports a valid PGN as a full history and closes', () => {
    const { onImport, onClose, textarea, load } = setup()
    fireEvent.change(textarea, { target: { value: '1. e4 e5 2. Nf3' } })
    fireEvent.click(load)
    expect(onImport).toHaveBeenCalledTimes(1)
    const parsed = onImport.mock.calls[0][0]
    expect(parsed.moves).toEqual(['e4', 'e5', 'Nf3'])
    expect(parsed.fens).toHaveLength(4)
    expect(onClose).toHaveBeenCalled()
  })

  it('shows an error and stays open for invalid input', () => {
    const { onImport, onClose, textarea, load } = setup()
    fireEvent.change(textarea, { target: { value: 'not chess at all 1. Zz9' } })
    fireEvent.click(load)
    expect(onImport).not.toHaveBeenCalled()
    expect(onClose).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent(/invalid pgn/i)
  })

  it('fills the textarea when a preset is chosen', () => {
    const { textarea } = setup()
    fireEvent.click(screen.getByRole('button', { name: /sicilian defense/i }))
    expect(textarea.value).toMatch(/2p5\/4P3/)
  })
})
