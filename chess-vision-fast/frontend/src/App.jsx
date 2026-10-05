import React, { useState, useRef, useEffect, useMemo } from 'react'
import { Chess } from 'chess.js'
import ChessBoard from './components/ChessBoard'
import EvalBar from './components/EvalBar'
import ImportModal from './components/ImportModal'
import UploadImage from './components/UploadImage'
import { bestMove, clearContext, getContext, getEngine } from './services/api'
import { START_FEN, setFenTurn } from './lib/chess'

const DEPTH_OPTIONS = [10, 15, 20]
const BOARD_OPTIONS = [
  { value: 'auto', label: 'Auto' },
  { value: 'front', label: 'Front' },
  { value: 'back', label: 'Back' },
]

export default function App() {
  // Chess instance
  const [chessGame] = useState(() => {
    const c = new Chess()
    try {
      c.load(START_FEN)
    } catch {
      c.reset()
    }
    return c
  })

  // Core state
  const [fen, setFen] = useState(START_FEN)
  const [turn, setTurn] = useState('w')
  const [depth, setDepth] = useState(15)
  const [boardOrientation, setBoardOrientation] = useState('auto')
  const [flipped, setFlipped] = useState(false)
  const [activeTab, setActiveTab] = useState('board') // 'board' | 'ocr'

  // Stockfish analysis state
  const [status, setStatus] = useState('Ready')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [bestMoveText, setBestMoveText] = useState('')
  const [bestMoveUci, setBestMoveUci] = useState('')
  const [scoreText, setScoreText] = useState('+0.00')
  const [evalScore, setEvalScore] = useState({ cp: 0, mate: null })
  const [lines, setLines] = useState([])
  const [overlayImage, setOverlayImage] = useState(null)

  // Move history and navigation
  const [historyFens, setHistoryFens] = useState([START_FEN])
  const [historyMoves, setHistoryMoves] = useState([])
  const [historyIndex, setHistoryIndex] = useState(0)

  // Engine info
  const [engineName, setEngineName] = useState(null)

  useEffect(() => {
    getEngine().then(data => {
      if (data && data.name) setEngineName(data.name)
    }).catch(() => {})
  }, [])

  // UI Modals
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [isInfoOpen, setIsInfoOpen] = useState(false)
  const [copiedFen, setCopiedFen] = useState(false)

  const abortControllerRef = useRef(null)

  const resolvedOrientation = useMemo(() => {
    return flipped ? 'back' : 'front'
  }, [flipped])

  // Copy FEN helper
  const handleCopyFen = () => {
    navigator.clipboard.writeText(fen)
    setCopiedFen(true)
    setTimeout(() => setCopiedFen(false), 2000)
  }

  // Toggle fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    } else {
      document.exitFullscreen().catch(() => {})
    }
  }

  // Stockfish analysis
  const runAnalysis = async (targetFen = fen, targetTurn = turn, targetDepth = depth) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setIsLoading(true)
    setError(null)
    setStatus(`Analyzing position with Stockfish (depth ${targetDepth})...`)

    try {
      const data = await bestMove(
        targetFen,
        abortControllerRef.current.signal,
        targetTurn,
        targetDepth
      )

      if (data.error) {
        setError(data.error)
        setStatus(`Error: ${data.error}`)
      } else {
        const uci = data.uci || ''
        const san = data.san || uci
        setBestMoveUci(uci)
        setBestMoveText(san)

        const scoreFormatted = data.score_text || (data.score?.cp != null ? `${(data.score.cp / 100).toFixed(2)}` : '+0.00')
        const sideLead = (data.score?.cp ?? 0) >= 0 ? 'White' : 'Black'
        setScoreText(`${scoreFormatted} ${sideLead}`)
        setEvalScore(data.score)

        if (data.lines && data.lines.length > 0) {
          setLines(data.lines)
        } else {
          setLines([
            {
              rank: 1,
              move: san,
              uci: uci,
              score_text: scoreFormatted,
              depth: targetDepth,
              nps: '1.2M nps',
              continuation: (data.pv || []).slice(1).join(' '),
            },
          ])
        }
        setStatus('Ready')
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setStatus('Analysis cancelled')
      } else {
        console.error(err)
        setError(err.message || 'Error communicating with analysis engine')
        setStatus('Engine error')
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  // Making a move on the interactive board
  const handleBoardMove = (from, to) => {
    try {
      const move = chessGame.move({ from, to, promotion: 'q' })
      if (move) {
        const newFen = chessGame.fen()
        setFen(newFen)
        setTurn(chessGame.turn())
        const newHistoryFens = historyFens.slice(0, historyIndex + 1)
        const newHistoryMoves = historyMoves.slice(0, historyIndex)
        newHistoryFens.push(newFen)
        newHistoryMoves.push(move.san)
        setHistoryFens(newHistoryFens)
        setHistoryMoves(newHistoryMoves)
        setHistoryIndex(newHistoryFens.length - 1)

        // Trigger analysis on new move
        runAnalysis(newFen, chessGame.turn(), depth)
      }
    } catch (err) {
      // Invalid move ignored
    }
  }

  // History navigation controls (|< < > >|)
  const goToMove = (index) => {
    if (index < 0 || index >= historyFens.length) return
    setHistoryIndex(index)
    const targetFen = historyFens[index]
    chessGame.load(targetFen)
    setFen(targetFen)
    setTurn(chessGame.turn())
    runAnalysis(targetFen, chessGame.turn(), depth)
  }

  // Import FEN or PGN
  const handleImport = (parsed) => {
    try {
      const newFen = parsed.fens[parsed.fens.length - 1]
      chessGame.load(newFen)
      setFen(newFen)
      setTurn(chessGame.turn())
      setHistoryFens(parsed.fens)
      setHistoryMoves(parsed.moves)
      setHistoryIndex(parsed.fens.length - 1)
      runAnalysis(newFen, chessGame.turn(), depth)
    } catch (err) {
      setError('Failed to import position: ' + err.message)
    }
  }

  // Reset/Clear board
  const handleClear = async () => {
    try {
      chessGame.reset()
      const newFen = chessGame.fen()
      setFen(newFen)
      setTurn('w')
      setBestMoveText('')
      setBestMoveUci('')
      setScoreText('+0.00')
      setEvalScore({ cp: 0, mate: null })
      setLines([])
      setHistoryFens([newFen])
      setHistoryMoves([])
      setHistoryIndex(0)
      setOverlayImage(null)
      setError(null)
      setStatus('Ready')
      await clearContext().catch(() => {})
    } catch (err) {
      console.error(err)
    }
  }

  // Download PGN or Board
  const handleDownload = () => {
    if (overlayImage) {
      const link = document.createElement('a')
      link.href = `data:image/png;base64,${overlayImage}`
      link.download = 'board-analysis.png'
      link.click()
      return
    }
    const pgnData = chessGame.pgn() || `[FEN "${fen}"]`
    const blob = new Blob([pgnData], { type: 'text/plain;charset=utf-8' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'game-analysis.pgn'
    link.click()
  }

  // OCR result handler
  const handleOcrResult = (data) => {
    if (data.fen) {
      try {
        chessGame.load(data.fen)
        setFen(data.fen)
        setTurn(chessGame.turn())
        setHistoryFens([data.fen])
        setHistoryMoves([])
        setHistoryIndex(0)
      } catch {}
    }
    if (data.overlay_image_base64) {
      setOverlayImage(data.overlay_image_base64)
    }
    if (data.uci) {
      setBestMoveUci(data.uci)
      setBestMoveText(data.san || data.uci)
    }
    if (data.lines && data.lines.length > 0) {
      setLines(data.lines)
    }
    if (data.score_text) {
      setScoreText(data.score_text)
    }
    if (data.error) {
      setError(data.error)
    } else {
      setError(null)
    }
    setActiveTab('board')
  }

  return (
    <div className="min-h-screen bg-[#0b121e] text-slate-100 flex flex-col font-sans select-none antialiased">
      {/* 1. Header Bar */}
      <header className="flex-shrink-0 px-5 py-2.5 bg-[#0e1626] border-b border-slate-800 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-wrap">
          {/* Badge */}
          <div className="inline-flex items-center gap-1.5 rounded-md bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-1">
            <svg className="w-3.5 h-3.5 text-emerald-400" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 19H5v-4h4v4zm0-6H5V9h4v4zm0-6H5V5h4v2zm6 12h-4v-4h4v4zm0-6h-4V9h4v4zm0-6h-4V5h4v2zm6 12h-4v-4h4v4zm0-6h-4V9h4v4zm0-6h-4V5h4v2z" />
            </svg>
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
              Chess Vision Fast
            </span>
          </div>

          {/* Title */}
          <h1 className="text-sm sm:text-base font-bold text-white flex items-center gap-1.5">
            Analysis with{' '}
            <span className="text-emerald-400 font-extrabold tracking-tight">
              {engineName || 'Stockfish'}
            </span>
          </h1>

          {/* Status Indicator Pill */}
          <div className="flex items-center gap-2 rounded-full bg-slate-900/80 border border-slate-700/60 px-3 py-1 text-xs text-slate-300">
            <span className="flex h-2 w-2 relative">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isLoading ? 'bg-amber-400' : 'bg-emerald-400'} opacity-75`}></span>
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isLoading ? 'bg-amber-400' : 'bg-emerald-500'}`}></span>
            </span>
            <span className="text-[11px] font-medium">{status}</span>
          </div>
        </div>

        {/* Right Header Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsImportOpen(true)}
            className="flex items-center gap-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/90 border border-slate-700/80 px-3 py-1.5 text-xs font-semibold text-slate-200 transition-all shadow-sm"
          >
            <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span>Import FEN / PGN</span>
          </button>

          <button
            onClick={() => setIsInfoOpen(!isInfoOpen)}
            title="Information"
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700/80 transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>

          <button
            onClick={toggleFullscreen}
            title="Fullscreen"
            className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700/80 transition-all"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>
      </header>

      {/* 2. Engine Settings Bar */}
      <section className="flex-shrink-0 px-5 py-2 bg-[#10192a] border-b border-slate-800/80 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-purple-500/20 text-purple-400 border border-purple-500/30">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <span className="text-xs font-bold text-white tracking-wide">Engine Settings</span>
        </div>

        {/* Center Controls: Depth, Board, Turn */}
        <div className="flex items-center gap-4 flex-wrap">
          {/* Depth */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Depth</span>
            <div className="flex items-center bg-slate-900/90 rounded-lg p-0.5 border border-slate-700/70">
              {DEPTH_OPTIONS.map((d) => (
                <button
                  key={d}
                  onClick={() => {
                    setDepth(d)
                    runAnalysis(fen, turn, d)
                  }}
                  className={`px-2.5 py-0.5 text-xs font-semibold rounded-md transition-all ${
                    depth === d
                      ? 'bg-emerald-500 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Board Orientation (Detector) */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400" title="Detector Orientation">OCR Dir</span>
            <div className="flex items-center bg-slate-900/90 rounded-lg p-0.5 border border-slate-700/70">
              {BOARD_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setBoardOrientation(opt.value)}
                  className={`px-2.5 py-0.5 text-xs font-semibold rounded-md transition-all ${
                    boardOrientation === opt.value
                      ? 'bg-emerald-500 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Turn */}
          <div className="flex items-center gap-1.5">
            <span className="text-xs text-slate-400">Turn</span>
            <div className="flex items-center bg-slate-900/90 rounded-lg p-0.5 border border-slate-700/70">
              <button
                onClick={() => {
                  try {
                    const newFen = setFenTurn(fen, 'w')
                    setFen(newFen)
                    setTurn('w')
                    runAnalysis(newFen, 'w', depth)
                  } catch (err) { setError(err.message) }
                }}
                className={`flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded-md transition-all ${
                  turn === 'w'
                    ? 'bg-emerald-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <div className={`w-1.5 h-1.5 rounded-full ${turn === 'w' ? 'bg-white' : 'bg-slate-500'}`}></div>
                <span>White</span>
              </button>
              <button
                onClick={() => {
                  try {
                    const newFen = setFenTurn(fen, 'b')
                    setFen(newFen)
                    setTurn('b')
                    runAnalysis(newFen, 'b', depth)
                  } catch (err) { setError(err.message) }
                }}
                className={`flex items-center gap-1 px-2.5 py-0.5 text-xs font-semibold rounded-md transition-all ${
                  turn === 'b'
                    ? 'bg-emerald-500 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <div className={`w-1.5 h-1.5 rounded-full ${turn === 'b' ? 'bg-white' : 'bg-slate-500'}`}></div>
                <span>Black</span>
              </button>
            </div>
          </div>

          {/* Threads & Hash specs */}
          <div className="hidden lg:flex items-center gap-2 text-xs text-slate-400 border-l border-slate-700 pl-3">
            <span>Threads: <strong className="text-slate-200">4</strong></span>
            <span>Hash: <strong className="text-slate-200">256MB</strong></span>
          </div>
        </div>
      </section>

      {/* 3. Sub-header Toolbar: Tabs & FEN row */}
      <div className="flex-shrink-0 px-5 py-2 bg-[#0c1322] border-b border-slate-800/80 flex items-center justify-between gap-4 flex-wrap">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('board')}
            className={`px-3.5 py-1 text-xs font-bold rounded-lg border transition-all ${
              activeTab === 'board'
                ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400 shadow-sm'
                : 'border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Interactive Board
          </button>
          <button
            onClick={() => setActiveTab('ocr')}
            className={`px-3.5 py-1 text-xs font-bold rounded-lg border transition-all ${
              activeTab === 'ocr'
                ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400 shadow-sm'
                : 'border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800/50'
            }`}
          >
            Upload / Screenshot OCR
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFlipped(!flipped)}
            className="flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 transition-all text-xs font-bold text-slate-300"
          >
            <svg className="w-3.5 h-3.5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
            </svg>
            Flip board
          </button>
        </div>

        {/* FEN Bar */}
        <div
          onClick={handleCopyFen}
          title="Click to copy FEN"
          className="flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-400 text-xs font-mono cursor-pointer hover:border-slate-700 hover:text-slate-200 transition-all max-w-full overflow-hidden"
        >
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0"></div>
          <span className="font-semibold text-slate-300">FEN:</span>
          <span className="truncate max-w-[280px] sm:max-w-[400px] md:max-w-[550px]">{fen}</span>
          <span className="text-[10px] text-emerald-400 font-sans ml-1 flex-shrink-0">
            {copiedFen ? 'Copied!' : 'Copy'}
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-4 sm:p-5 flex flex-col gap-4 max-w-7xl mx-auto w-full">
        {activeTab === 'board' ? (
          /* Dual column board & evaluation layout */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
            {/* Left Column: Vertical EvalBar + ChessBoard (7 cols) */}
            <div className="lg:col-span-7 flex items-center justify-center gap-1 bg-[#10192a]/90 rounded-2xl border border-slate-800/90 p-4 sm:p-6 shadow-xl relative min-h-[460px]">
              {/* Eval Bar on the left */}
              <div className="h-[380px] sm:h-[440px] flex-shrink-0">
                <EvalBar score={evalScore} scoreText={scoreText} />
              </div>

              {/* Centered Board */}
              <div className="flex-1 flex justify-center items-center">
                {overlayImage ? (
                  <div className="relative max-w-[440px] aspect-square rounded-2xl overflow-hidden border border-slate-700">
                    <img
                      src={`data:image/png;base64,${overlayImage}`}
                      alt="Analyzed board"
                      className="w-full h-full object-contain"
                    />
                    <button
                      onClick={() => setOverlayImage(null)}
                      className="absolute top-2 right-2 px-2 py-1 bg-slate-900/90 border border-slate-700 text-xs font-semibold rounded text-slate-300 hover:text-white"
                    >
                      Show Interactive
                    </button>
                  </div>
                ) : (
                  <ChessBoard
                    fen={fen}
                    bestMove={bestMoveText}
                    bestMoveUci={bestMoveUci}
                    scoreText={scoreText}
                    orientation={resolvedOrientation}
                    onMove={handleBoardMove}
                  />
                )}
              </div>
            </div>

            {/* Right Column: Live Evaluation & Move Log Panels (5 cols) */}
            <div className="lg:col-span-5 flex flex-col gap-4">
              {/* Panel 1: LIVE EVALUATION */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#10192a]/90 p-4 shadow-xl">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Live Evaluation
                    </h3>
                  </div>
                  <div className="rounded-md bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-0.5 text-xs font-bold font-mono text-emerald-400">
                    {scoreText}
                  </div>
                </div>

                {/* Candidate Lines */}
                <div className="space-y-2.5">
                  {lines.map((line, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-slate-800 bg-[#0d1524] p-2.5 hover:border-slate-700 transition-all font-mono"
                    >
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-bold text-emerald-400">
                          {line.rank}. {line.move}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          {line.depth ? `d:${line.depth}` : ''} {line.nps ? `• ${line.nps}` : ''}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 tracking-wide break-words">
                        {line.continuation || line.move}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Panel 2: MOVE LOG (PGN) */}
              <div className="rounded-2xl border border-slate-800/90 bg-[#10192a]/90 p-4 shadow-xl flex flex-col">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                    Move Log (PGN)
                  </h3>
                  <span className="text-xs font-mono text-slate-400">
                    Ply: <strong className="text-slate-200">{historyMoves.length}</strong>
                  </span>
                </div>

                {/* Moves List table */}
                <div className="min-h-[80px] max-h-[140px] overflow-y-auto font-mono text-xs text-slate-300 space-y-1 pr-1">
                  {historyMoves.length === 0 ? (
                    <div className="text-slate-500 italic py-2">No moves recorded yet</div>
                  ) : (
                    Array.from({ length: Math.ceil(historyMoves.length / 2) }).map((_, i) => {
                      const whiteMove = historyMoves[i * 2]
                      const blackMove = historyMoves[i * 2 + 1]
                      return (
                        <div key={i} className="flex items-center py-0.5 border-b border-slate-800/40">
                          <span className="w-10 text-slate-500 font-semibold">{i + 1}.</span>
                          <span className="w-24 text-emerald-400 font-medium">{whiteMove}</span>
                          <span className="w-24 text-slate-300 font-medium">{blackMove || '...'}</span>
                        </div>
                      )
                    })
                  )}
                </div>

                {/* Navigation Buttons: |<  <  >  >| */}
                <div className="flex items-center justify-center gap-6 pt-3 mt-3 border-t border-slate-800 text-slate-400">
                  <button
                    onClick={() => goToMove(0)}
                    disabled={historyIndex === 0}
                    title="First move"
                    className="hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 text-sm font-bold transition-all px-1.5 py-0.5 rounded"
                  >
                    |&lt;
                  </button>
                  <button
                    onClick={() => goToMove(historyIndex - 1)}
                    disabled={historyIndex === 0}
                    title="Previous move"
                    className="hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 text-sm font-bold transition-all px-1.5 py-0.5 rounded"
                  >
                    &lt;
                  </button>
                  <button
                    onClick={() => goToMove(historyIndex + 1)}
                    disabled={historyIndex >= historyFens.length - 1}
                    title="Next move"
                    className="hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 text-sm font-bold transition-all px-1.5 py-0.5 rounded"
                  >
                    &gt;
                  </button>
                  <button
                    onClick={() => goToMove(historyFens.length - 1)}
                    disabled={historyIndex >= historyFens.length - 1}
                    title="Last move"
                    className="hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 text-sm font-bold transition-all px-1.5 py-0.5 rounded"
                  >
                    &gt;|
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {/* 4. Upload Image (Board Recognition) Area */}
        <section className="rounded-2xl border border-slate-800/90 bg-[#10192a]/90 p-4 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h2 className="text-xs font-bold text-white tracking-wide">
                Upload Image (Board Recognition)
              </h2>
            </div>
            <span className="text-[11px] font-medium text-slate-400">
              Instant PNG / JPG OCR
            </span>
          </div>

          <UploadImage
            onResult={handleOcrResult}
            setStatus={setStatus}
            setIsLoading={setIsLoading}
            abortControllerRef={abortControllerRef}
            orientation={resolvedOrientation}
            turn={turn}
            depth={depth}
          />
        </section>

        {/* 5. Bottom Controls Bar */}
        <section className="rounded-2xl border border-slate-800/90 bg-[#10192a]/90 p-3.5 shadow-xl flex flex-col gap-2">
          <div className="flex items-center gap-2 mb-1">
            <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
            <span className="text-xs font-bold tracking-wider text-slate-200">CONTROLS</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
            {/* Analyze button (Green) */}
            <button
              onClick={() => runAnalysis(fen, turn, depth)}
              disabled={isLoading}
              className="sm:col-span-3 h-11 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/30 transition-all cursor-pointer"
            >
              <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
              <span>Analyze</span>
            </button>

            {/* Download button (Dark slate) */}
            <button
              onClick={handleDownload}
              className="sm:col-span-3 h-11 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 border border-slate-700/80 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Download</span>
            </button>

            {/* Moves info pill */}
            <div className="sm:col-span-3 h-11 rounded-xl bg-[#0d1524] border border-slate-800 px-3 flex flex-col justify-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 leading-none">MOVES</span>
              <span className="text-xs font-semibold text-slate-200 mt-0.5 truncate">
                {historyMoves.length > 0 ? `1. ${historyMoves[0]} (${historyMoves.length} move played)` : '0 moves played'}
              </span>
            </div>

            {/* Clear button (Red) */}
            <button
              onClick={handleClear}
              className="sm:col-span-3 h-11 rounded-xl bg-[#dc2626] hover:bg-[#b91c1c] text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-red-950/30 transition-all cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span>Clear</span>
            </button>
          </div>
        </section>

        {/* Error notification */}
        {error && (
          <div className="rounded-xl border border-red-500/40 bg-red-500/15 p-3 text-xs text-red-300 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-white font-bold ml-2">
              ✕
            </button>
          </div>
        )}
      </main>

      {/* Import Modal */}
      <ImportModal
        isOpen={isImportOpen}
        onClose={() => setIsImportOpen(false)}
        onImport={handleImport}
      />

      {/* Info Modal */}
      {isInfoOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white">About Chess Vision Fast</h3>
              <button onClick={() => setIsInfoOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="mt-3 text-xs text-slate-300 space-y-2 leading-relaxed">
              <p>
                <strong>Chess Vision Fast</strong> combines real-time Computer Vision board recognition with <strong>Stockfish NNUE</strong> for deep positional evaluation.
              </p>
              <ul className="list-disc pl-4 space-y-1 text-slate-400">
                <li>Click any piece on the board to make moves.</li>
                <li>Analyze depth: switch between 10, 15, and 20 half-moves.</li>
                <li>Live evaluation displays the top 3 candidate engine continuations.</li>
                <li>Drag & drop a screenshot or paste from clipboard to parse boards with OCR.</li>
              </ul>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setIsInfoOpen(false)}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
