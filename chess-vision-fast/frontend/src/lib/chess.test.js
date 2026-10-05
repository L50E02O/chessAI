import { describe, expect, it } from 'vitest'
import {
  START_FEN,
  evalToWhitePercent,
  formatScore,
  parseImport,
  setFenTurn,
} from './chess'

describe('parseImport', () => {
  it('loads a FEN as a single position with no moves', () => {
    const fen = 'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2'
    expect(parseImport(fen)).toEqual({ fens: [fen], moves: [] })
  })

  it('builds one FEN per ply from a PGN', () => {
    const result = parseImport('1. e4 e5 2. Nf3 Nc6')
    expect(result.moves).toEqual(['e4', 'e5', 'Nf3', 'Nc6'])
    expect(result.fens).toHaveLength(5)
    expect(result.fens[0]).toBe(START_FEN)
    expect(result.fens[1]).toBe('rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1')
  })

  it('accepts a PGN with headers and a result', () => {
    const pgn = '[Event "Casual"]\n[White "A"]\n[Black "B"]\n\n1. d4 d5 2. c4 1-0'
    expect(parseImport(pgn).moves).toEqual(['d4', 'd5', 'c4'])
  })

  it('starts a PGN from its [FEN] header', () => {
    const start = '4k3/8/8/8/8/8/4P3/4K3 w - - 0 1'
    const pgn = `[SetUp "1"]\n[FEN "${start}"]\n\n1. e4 Kd7`
    const result = parseImport(pgn)
    expect(result.fens[0]).toBe(start)
    expect(result.moves).toEqual(['e4', 'Kd7'])
  })

  it('rejects empty input', () => {
    expect(() => parseImport('   ')).toThrow(/paste a FEN or PGN/i)
  })

  it('rejects an invalid FEN with a readable message', () => {
    expect(() => parseImport('rnbqkbnr/pppppppp/8/8 w')).toThrow(/invalid fen/i)
  })

  it('rejects an invalid PGN with a readable message', () => {
    expect(() => parseImport('1. e4 e5 2. Ke3 Qxz9')).toThrow(/invalid pgn/i)
  })
})

describe('setFenTurn', () => {
  it('switches side to move and clears en passant', () => {
    const fen = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
    expect(setFenTurn(fen, 'w')).toBe('rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1')
  })

  it('returns the same FEN when the side is unchanged', () => {
    expect(setFenTurn(START_FEN, 'w')).toBe(START_FEN)
  })

  it('throws when the side not to move would be in check', () => {
    // Black king on e8 attacked by the rook on e1: it cannot be White to move.
    expect(() => setFenTurn('4k3/8/8/8/8/8/8/K3R3 b - - 0 1', 'w')).toThrow()
  })
})

describe('formatScore', () => {
  it('formats centipawns from White perspective', () => {
    expect(formatScore({ cp: 142, mate: null })).toBe('+1.42')
    expect(formatScore({ cp: -30, mate: null })).toBe('-0.30')
    expect(formatScore({ cp: 0, mate: null })).toBe('0.00')
  })

  it('formats mates', () => {
    expect(formatScore({ cp: null, mate: 3 })).toBe('M3')
    expect(formatScore({ cp: null, mate: -2 })).toBe('-M2')
  })

  it('handles missing scores', () => {
    expect(formatScore(null)).toBe('0.00')
    expect(formatScore({ cp: null, mate: null })).toBe('0.00')
  })
})

describe('evalToWhitePercent', () => {
  it('is 50 for an even or unknown position', () => {
    expect(evalToWhitePercent(null)).toBe(50)
    expect(evalToWhitePercent({ cp: 0, mate: null })).toBe(50)
  })

  it('is full or empty for mates', () => {
    expect(evalToWhitePercent({ cp: null, mate: 2 })).toBe(100)
    expect(evalToWhitePercent({ cp: null, mate: -1 })).toBe(0)
  })

  it('grows with advantage and is clamped to 5..95', () => {
    const small = evalToWhitePercent({ cp: 100, mate: null })
    const big = evalToWhitePercent({ cp: 400, mate: null })
    expect(small).toBeGreaterThan(50)
    expect(big).toBeGreaterThan(small)
    expect(evalToWhitePercent({ cp: 5000, mate: null })).toBe(95)
    expect(evalToWhitePercent({ cp: -5000, mate: null })).toBe(5)
  })
})
