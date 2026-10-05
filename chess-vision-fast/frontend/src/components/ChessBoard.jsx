import React, { useState } from 'react'
import { ChessPiece } from './ChessPiece'

const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
const RANKS = ['8', '7', '6', '5', '4', '3', '2', '1']

export default function ChessBoard({
  boardState, // 8x8 array or chess instance
  fen,
  bestMove, // e.g. "g1f3" or "Nf3"
  bestMoveUci, // e.g. "g1f3"
  scoreText, // e.g. "+1.42"
  orientation = 'front', // 'front' (white bottom) or 'back' (black bottom)
  onMove,
  interactive = true,
}) {
  const [selectedSquare, setSelectedSquare] = useState(null)

  // Parse FEN into an 8x8 grid of pieces
  const fenParts = (fen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1').split(' ')
  const piecePlacement = fenParts[0]

  const grid = []
  const rows = piecePlacement.split('/')
  for (let r = 0; r < 8; r++) {
    const row = []
    const rowStr = rows[r] || '8'
    for (let i = 0; i < rowStr.length; i++) {
      const char = rowStr[i]
      if (char >= '1' && char <= '8') {
        const count = parseInt(char, 10)
        for (let c = 0; c < count; c++) row.push(null)
      } else {
        row.push(char)
      }
    }
    grid.push(row)
  }

  // Parse best move UCI (e.g. "g1f3", "e2e4")
  let moveFrom = null
  let moveTo = null
  if (bestMoveUci && bestMoveUci.length >= 4) {
    moveFrom = bestMoveUci.slice(0, 2).toLowerCase()
    moveTo = bestMoveUci.slice(2, 4).toLowerCase()
  }

  const isFlipped = orientation === 'back'
  const displayRanks = isFlipped ? [...RANKS].reverse() : RANKS
  const displayFiles = isFlipped ? [...FILES].reverse() : FILES

  const getSquareCoord = (squareStr) => {
    if (!squareStr || squareStr.length < 2) return null
    const f = squareStr[0].toLowerCase()
    const r = squareStr[1]
    const fileIdx = displayFiles.indexOf(f)
    const rankIdx = displayRanks.indexOf(r)
    if (fileIdx === -1 || rankIdx === -1) return null
    return {
      x: (fileIdx + 0.5) * 12.5, // percent 0..100
      y: (rankIdx + 0.5) * 12.5,
    }
  }

  const handleSquareClick = (squareKey, piece) => {
    if (!interactive) return

    if (selectedSquare) {
      if (selectedSquare === squareKey) {
        setSelectedSquare(null)
      } else {
        if (onMove) {
          onMove(selectedSquare, squareKey)
        }
        setSelectedSquare(null)
      }
    } else {
      if (piece) {
        setSelectedSquare(squareKey)
      }
    }
  }

  const fromCoords = moveFrom ? getSquareCoord(moveFrom) : null
  const toCoords = moveTo ? getSquareCoord(moveTo) : null

  // Arrow calculation
  let arrowSvg = null
  if (fromCoords && toCoords) {
    // Determine arrow path: slight curve if knight or direct line
    const dx = toCoords.x - fromCoords.x
    const dy = toCoords.y - fromCoords.y
    const isKnight = (Math.abs(dx) > 10 && Math.abs(dy) > 15) || (Math.abs(dx) > 15 && Math.abs(dy) > 10)

    let pathD = `M ${fromCoords.x} ${fromCoords.y} L ${toCoords.x} ${toCoords.y}`
    if (isKnight) {
      // Curved arc
      const cx = (fromCoords.x + toCoords.x) / 2 + (dy > 0 ? -6 : 6)
      const cy = (fromCoords.y + toCoords.y) / 2 + (dx > 0 ? 6 : -6)
      pathD = `M ${fromCoords.x} ${fromCoords.y} Q ${cx} ${cy} ${toCoords.x} ${toCoords.y}`
    }

    arrowSvg = (
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none z-20"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="4"
            markerHeight="4"
            refX="3"
            refY="2"
            orient="auto"
          >
            <polygon points="0 0, 4 2, 0 4" fill="#10b981" />
          </marker>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="0.8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <path
          d={pathD}
          fill="none"
          stroke="#10b981"
          strokeWidth="1.8"
          strokeLinecap="round"
          markerEnd="url(#arrowhead)"
          filter="url(#glow)"
        />
      </svg>
    )
  }

  return (
    <div className="relative w-full max-w-[500px] aspect-square select-none">
      {/* Best Move Floating Badge */}
      {bestMove && (
        <div className="absolute top-2.5 left-1/2 -translate-x-1/2 z-30 flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900/90 border border-emerald-500/50 shadow-lg backdrop-blur-md">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-bold text-emerald-400">
            Best Move: <span className="text-white">{bestMove}</span> {scoreText && `(${scoreText})`}
          </span>
        </div>
      )}

      {/* Board Outer Container */}
      <div className="w-full h-full rounded-2xl overflow-hidden shadow-2xl border border-slate-700/60 bg-slate-900/80 p-2.5 flex flex-col justify-center">
        <div className="relative w-full h-full rounded-xl overflow-hidden grid grid-rows-8 grid-cols-8 shadow-inner">
          {displayRanks.map((rank, rIdx) => {
            const actualRankIdx = 8 - parseInt(rank, 10)
            return displayFiles.map((file, fIdx) => {
              const actualFileIdx = FILES.indexOf(file)
              const square = `${file}${rank}`
              const isLight = (rIdx + fIdx) % 2 === 0

              const piece = grid[actualRankIdx] ? grid[actualRankIdx][actualFileIdx] : null

              const isSelected = selectedSquare === square
              const isMoveFrom = moveFrom === square
              const isMoveTo = moveTo === square

              return (
                <div
                  key={square}
                  onClick={() => handleSquareClick(square, piece)}
                  className={`relative flex items-center justify-center cursor-pointer transition-colors duration-150 ${
                    isLight ? 'bg-[#cbd5e1]' : 'bg-[#64748b]'
                  } ${isMoveFrom ? '!bg-emerald-500/50' : ''} ${
                    isMoveTo ? '!bg-teal-500/40' : ''
                  } ${isSelected ? '!bg-amber-400/50 ring-2 ring-amber-400 ring-inset' : ''}`}
                >
                  {/* Rank Label on left column */}
                  {fIdx === 0 && (
                    <span
                      className={`absolute top-0.5 left-1 text-[10px] font-semibold leading-none pointer-events-none ${
                        isLight ? 'text-slate-600' : 'text-slate-300'
                      }`}
                    >
                      {rank}
                    </span>
                  )}

                  {/* File Label on bottom row */}
                  {rIdx === 7 && (
                    <span
                      className={`absolute bottom-0.5 right-1 text-[10px] font-semibold leading-none pointer-events-none ${
                        isLight ? 'text-slate-600' : 'text-slate-300'
                      }`}
                    >
                      {file}
                    </span>
                  )}

                  {/* Target Square Indicator Dot */}
                  {isMoveTo && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-5 h-5 rounded-full bg-emerald-500/80 border-2 border-white shadow-md flex items-center justify-center">
                        <div className="w-1.5 h-1.5 rounded-full bg-slate-900"></div>
                      </div>
                    </div>
                  )}

                  {/* Piece */}
                  {piece && (
                    <div className="relative z-10 w-[82%] h-[82%] transition-transform hover:scale-105 active:scale-95">
                      <ChessPiece piece={piece} />
                    </div>
                  )}
                </div>
              )
            })
          })}

          {/* SVG Arrow Overlay */}
          {arrowSvg}
        </div>
      </div>
    </div>
  )
}
