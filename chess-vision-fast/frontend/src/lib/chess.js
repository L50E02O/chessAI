import { Chess } from 'chess.js'

export const START_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

function looksLikeFen(text) {
  return !text.includes('[') && text.split(/\s+/)[0].includes('/')
}

/**
 * Parse user input (FEN or PGN) into a navigable history.
 * @returns {{ fens: string[], moves: string[] }} fens.length === moves.length + 1
 * @throws {Error} with a readable message when the input is empty or invalid.
 */
export function parseImport(text) {
  const input = (text || '').trim()
  if (!input) {
    throw new Error('Please paste a FEN or PGN.')
  }

  if (looksLikeFen(input)) {
    try {
      const game = new Chess(input)
      return { fens: [game.fen()], moves: [] }
    } catch (err) {
      throw new Error(`Invalid FEN: ${err.message}`)
    }
  }

  const game = new Chess()
  try {
    game.loadPgn(input)
  } catch (err) {
    throw new Error(`Invalid PGN: ${err.message}`)
  }
  const verbose = game.history({ verbose: true })
  if (verbose.length === 0) {
    return { fens: [game.fen()], moves: [] }
  }
  return {
    fens: [verbose[0].before, ...verbose.map((m) => m.after)],
    moves: verbose.map((m) => m.san),
  }
}

/**
 * Return `fen` with `color` ('w' | 'b') to move and en passant cleared.
 * @throws {Error} if the side currently to move is in check (it cannot become the side not to move).
 */
export function setFenTurn(fen, color) {
  const current = new Chess(fen)
  if (current.turn() === color) return fen
  if (current.inCheck()) {
    throw new Error('Cannot switch turn: the side to move is in check.')
  }
  const parts = fen.trim().split(/\s+/)
  parts[1] = color
  parts[3] = '-'
  const next = parts.join(' ')
  new Chess(next) // validate
  return next
}

/** Format an engine score ({cp, mate}, White perspective) as text. */
export function formatScore(score) {
  if (score && score.mate != null) {
    return score.mate > 0 ? `M${score.mate}` : `-M${Math.abs(score.mate)}`
  }
  if (score && score.cp != null) {
    if (score.cp === 0) return '0.00'
    const value = (score.cp / 100).toFixed(2)
    return score.cp > 0 ? `+${value}` : value
  }
  return '0.00'
}

/** Map an engine score to the White share of the eval bar (0..100). */
export function evalToWhitePercent(score) {
  if (!score) return 50
  if (score.mate != null) return score.mate > 0 ? 100 : 0
  if (score.cp == null) return 50
  const winning = 2 / (1 + Math.exp(-score.cp / 400)) - 1 // -1..1
  return Math.min(95, Math.max(5, 50 + 50 * winning))
}
