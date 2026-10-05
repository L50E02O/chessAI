import React from 'react'

// High-fidelity standard vector chess pieces (cburnett / lichess SVG paths)
export const ChessPiece = ({ piece, className = 'w-full h-full' }) => {
  if (!piece) return null

  const isWhite = piece === piece.toUpperCase()
  const type = piece.toLowerCase()

  const strokeColor = isWhite ? '#000000' : '#ececec'
  const fillColor = isWhite ? '#ffffff' : '#1e2024'
  const accentColor = isWhite ? '#000000' : '#ececec'

  switch (type) {
    case 'p': // Pawn
      return (
        <svg viewBox="0 0 45 45" className={className} xmlns="http://www.w3.org/2000/svg">
          <path
            d="m 22.5,9 c -2.21,0 -4,1.79 -4,4 0,0.89 0.29,1.71 0.78,2.38 C 17.33,16.5 16,18.59 16,21 c 0,2.03 0.94,3.84 2.41,5.03 C 15.41,27.09 11,31.58 11,39.5 L 34,39.5 C 34,31.58 29.59,27.09 26.59,26.03 28.06,24.84 29,23.03 29,21 29,18.59 27.67,16.5 25.72,15.38 26.21,14.71 26.5,13.89 26.5,13 26.5,10.79 24.71,9 22.5,9 z"
            fill={fillColor}
            stroke={strokeColor}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )
    case 'r': // Rook
      return (
        <svg viewBox="0 0 45 45" className={className} xmlns="http://www.w3.org/2000/svg">
          <g fill={fillColor} stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M 9,39 L 36,39 L 36,36 L 9,36 L 9,39 z" />
            <path d="M 12,36 L 12,32 L 33,32 L 33,36 L 12,36 z" />
            <path d="M 11,14 L 11,9 L 15,9 L 15,11 L 20,11 L 20,9 L 25,9 L 25,11 L 30,11 L 30,9 L 34,9 L 34,14" />
            <path d="M 34,14 L 31,17 L 14,17 L 11,14" />
            <path d="M 31,17 L 31,29.5 L 14,29.5 L 14,17" />
            <path d="M 31,29.5 L 32.5,32 L 12.5,32 L 14,29.5" />
            <path d="M 11,14 L 34,14" strokeWidth="1" />
          </g>
        </svg>
      )
    case 'n': // Knight
      return (
        <svg viewBox="0 0 45 45" className={className} xmlns="http://www.w3.org/2000/svg">
          <g fill={fillColor} stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M 22,10 C 32.5,11 38.5,18 38,39 L 15,39 C 15,30 25,32.5 23,18" />
            <path d="M 24,18 C 24.38,20.91 18.45,25.37 16,27 C 13,29 13.18,31.34 11,31 C 9.958,30.06 12.41,27.96 11,28 C 10,28 11.19,29.23 10,30 C 9,30 5.997,31 6,26 C 6,24 12,14 12,14 C 12,14 13.89,12.1 14,10.5 C 13.27,7.4 17.05,5.14 19.5,6.5 C 20,7.5 19.45,9.04 19,10 C 20.5,9.5 21,9.5 22,10 z" />
            <circle cx="15" cy="14" r="1.5" fill={accentColor} stroke="none" />
            <path d="M 9.5 25.5 A 0.5 0.5 0 1 1 8.5,25.5 A 0.5 0.5 0 1 1 9.5 25.5 z" fill={accentColor} stroke="none" />
          </g>
        </svg>
      )
    case 'b': // Bishop
      return (
        <svg viewBox="0 0 45 45" className={className} xmlns="http://www.w3.org/2000/svg">
          <g fill={fillColor} stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M 9,36 C 12.39,35.03 19.11,36.43 22.5,34 C 25.89,36.43 32.61,35.03 36,36 C 36,36 37.65,36.54 39,38 C 38.32,38.97 37.35,38.99 36,38.5 C 32.61,37.53 25.89,38.96 22.5,37.5 C 19.11,38.96 12.39,37.53 9,38.5 C 7.646,38.99 6.677,38.97 6,38 C 7.354,36.54 9,36 9,36 z" />
            <path d="M 15,32 C 17.5,34.5 27.5,34.5 30,32 C 30.5,30.5 30,30 30,30 C 30,27.5 27.5,26 27.5,26 C 33,24.5 33.5,14.5 22.5,10.5 C 11.5,14.5 12,24.5 17.5,26 C 17.5,26 15,27.5 15,30 C 15,30 14.5,30.5 15,32 z" />
            <path d="M 25 8 A 2.5 2.5 0 1 1 20,8 A 2.5 2.5 0 1 1 25 8 z" />
            <path d="M 17.5,26 L 27.5,26 M 15,30 L 30,30" strokeWidth="1" />
            <path d="M 22.5,15.5 L 22.5,20.5 M 20,18 L 25,18" stroke={strokeColor} strokeWidth="1" />
          </g>
        </svg>
      )
    case 'q': // Queen
      return (
        <svg viewBox="0 0 45 45" className={className} xmlns="http://www.w3.org/2000/svg">
          <g fill={fillColor} stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M 9 13 A 2 2 0 1 1 5,13 A 2 2 0 1 1 9 13 z" />
            <path d="M 24 9 A 2 2 0 1 1 20,9 A 2 2 0 1 1 24 9 z" />
            <path d="M 39 13 A 2 2 0 1 1 35,13 A 2 2 0 1 1 39 13 z" />
            <path d="M 16 10.5 A 1.5 1.5 0 1 1 13,10.5 A 1.5 1.5 0 1 1 16 10.5 z" />
            <path d="M 31 10.5 A 1.5 1.5 0 1 1 28,10.5 A 1.5 1.5 0 1 1 31 10.5 z" />
            <path d="M 9,26 C 17.5,24.5 30,24.5 36,26 L 38.5,13.5 L 31,25 L 22.5,10 L 14,25 L 6.5,13.5 L 9,26 z" />
            <path d="M 9,26 C 9,28 10.5,28 11.5,30 C 12.5,31.5 12.5,31 12,33.5 C 10.5,34.5 10.5,36 10.5,36 C 9,37.5 11,38.5 11,38.5 L 34,38.5 C 34,38.5 36,37.5 34.5,36 C 34.5,36 34.5,34.5 33,33.5 C 32.5,31 32.5,31.5 33.5,30 C 34.5,28 36,28 36,26" />
            <path d="M 11.5,30 C 15,29 30,29 33.5,30" strokeWidth="1" />
            <path d="M 12,33.5 C 18,32.5 27,32.5 33,33.5" strokeWidth="1" />
          </g>
        </svg>
      )
    case 'k': // King
      return (
        <svg viewBox="0 0 45 45" className={className} xmlns="http://www.w3.org/2000/svg">
          <g fill={fillColor} stroke={strokeColor} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M 22.5,11.5 L 22.5,6 M 20,8 L 25,8" strokeWidth="1.5" />
            <path d="M 9,26 C 17.5,23.5 27.5,23.5 36,26 C 36,26 38,20.5 38,16 C 38,13 36,13 36,13 C 34,13 32.5,14.5 31,16 C 29.5,14.5 28,13 26,13 C 24,13 22.5,14.5 22.5,16 C 22.5,14.5 21,13 19,13 C 17,13 15.5,14.5 14,16 C 12.5,14.5 11,13 9,13 C 9,13 7,13 7,16 C 7,20.5 9,26 9,26 z" />
            <path d="M 11.5,30 C 15,29 30,29 33.5,30" strokeWidth="1" />
            <path d="M 12,33.5 C 18,32.5 27,32.5 33,33.5" strokeWidth="1" />
            <path d="M 9,26 C 9,28 10.5,28 11.5,30 C 12.5,31.5 12.5,31 12,33.5 C 10.5,34.5 10.5,36 10.5,36 C 9,37.5 11,38.5 11,38.5 L 34,38.5 C 34,38.5 36,37.5 34.5,36 C 34.5,36 34.5,34.5 33,33.5 C 32.5,31 32.5,31.5 33.5,30 C 34.5,28 36,28 36,26" />
          </g>
        </svg>
      )
    default:
      return null
  }
}
