import React, { useState, useRef, useEffect } from 'react'
import UploadImage from './components/UploadImage'
import BoardPreview from './components/BoardPreview'
import { bestMove, clearContext, getContext } from './services/api'

const DEPTHS = [10, 15, 20]

export default function App() {
  const [status, setStatus] = useState('Ready to analyze')
  const [overlayImage, setOverlayImage] = useState(null)
  const [fen, setFen] = useState('')
  const [bestMoveText, setBestMoveText] = useState('')
  const [evaluationText, setEvaluationText] = useState('')
  const [score, setScore] = useState(null)
  const [pv, setPv] = useState([])
  const [confidence, setConfidence] = useState(null)
  const [fenWarnings, setFenWarnings] = useState([])
  const [moveHistory, setMoveHistory] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [orientation, setOrientation] = useState('auto')
  const [turn, setTurn] = useState('w')
  const [depth, setDepth] = useState(15)
  const abortControllerRef = useRef(null)

  useEffect(() => {
    getContext()
      .then(data => {
        if (data && Array.isArray(data.move_history)) {
          setMoveHistory(data.move_history)
        }
      })
      .catch(() => {})
  }, [])

  const cancelOperation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsLoading(false)
    setStatus('Operation cancelled')
    setError(null)
  }

  const handleResult = (data) => {
    setFen(data.fen || '')
    setOverlayImage(data.overlay_image_base64 || data.board_image_base64 || null)
    setBestMoveText(data.best_move || data.uci || '')
    setEvaluationText(data.evaluation_text || '')
    setScore(data.score || null)
    setPv(data.pv || [])
    setConfidence(data.confidence)
    setFenWarnings(data.fen_warnings || [])
    if (data.orientation && data.orientation !== 'w-bottom') {
      setOrientation(data.orientation === 'w-top' ? 'back' : 'auto')
    }
    if (data.error) {
      setError(data.error)
      setStatus(`Error: ${data.error}`)
    } else {
      setError(null)
      setStatus('Analysis completed')
    }
    setIsLoading(false)
    getContext().then(ctx => {
      if (ctx && Array.isArray(ctx.move_history)) setMoveHistory(ctx.move_history)
    }).catch(() => {})
  }

  const handleManualBestMove = async () => {
    if (!fen) {
      setStatus('First upload a board image')
      setError('No FEN available')
      return
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)
    setStatus(`Analyzing with Stockfish (depth ${depth})...`)
    try {
      const response = await bestMove(fen, abortControllerRef.current.signal, turn, depth)
      setBestMoveText(response.uci || '')
      setEvaluationText(response.evaluation_text || '')
      setScore(response.score || null)
      setPv(response.pv || [])
      setFenWarnings(response.fen_warnings || [])
      if (response.error) {
        setError(response.error)
        setStatus(`Error: ${response.error}`)
      } else {
        setError(null)
        setStatus('Analysis completed')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Analysis cancelled')
        setError(null)
      } else {
        console.error(error)
        const errorMsg = error.message || 'Error analyzing position'
        setError(errorMsg)
        setStatus(`Error: ${errorMsg}`)
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  const handleClearContext = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)
    setStatus('Clearing context...')
    try {
      await clearContext(abortControllerRef.current.signal)
      setFen('')
      setBestMoveText('')
      setEvaluationText('')
      setScore(null)
      setPv([])
      setFenWarnings([])
      setOverlayImage(null)
      setMoveHistory([])
      setError(null)
      setStatus('Context cleared - Ready for new game')
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Operation cancelled')
        setError(null)
      } else {
        console.error(error)
        setError(error.message || 'Error clearing context')
        setStatus('Error clearing context')
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  const downloadOverlay = () => {
    if (!overlayImage) return
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${overlayImage}`
    link.download = 'analyzed-board.png'
    link.click()
  }

  const toggleOrientation = (value) => {
    setOrientation(value)
    setStatus(value === 'auto' ? 'Orientation: auto' : `Orientation: ${value}`)
  }

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      <header className="flex-shrink-0 px-4 py-2 text-center border-b border-slate-700/50">
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <div className="inline-block rounded-full bg-emerald-500/20 px-2 py-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Chess Vision Fast</p>
          </div>
          <h1 className="text-lg sm:text-xl font-bold text-white">
            Analysis with{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
              Stockfish
            </span>
          </h1>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <div className={`h-1.5 w-1.5 rounded-full ${isLoading ? 'bg-yellow-500 animate-pulse' : error ? 'bg-red-500' : 'bg-emerald-500'}`}></div>
            <span className="hidden sm:inline">{status}</span>
          </div>
          {isLoading && (
            <button
              onClick={cancelOperation}
              className="ml-2 rounded bg-red-500/20 hover:bg-red-500/30 px-2 py-1 text-xs font-semibold text-red-400 transition-all flex items-center gap-1"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Cancel
            </button>
          )}
        </div>
        {error && (
          <div className="mt-1 text-xs text-red-400 bg-red-500/10 rounded px-2 py-1 inline-block">
            {error}
          </div>
        )}
      </header>

      <main className="flex-1 overflow-hidden px-4 py-2">
        <div className="h-full flex flex-col gap-2 max-w-7xl mx-auto">
          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-2 shadow-xl">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-xs font-semibold text-white">Engine Settings</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Depth</span>
                  {DEPTHS.map((d) => (
                    <button
                      key={d}
                      onClick={() => setDepth(d)}
                      disabled={isLoading}
                      className={`px-2 py-1 text-xs font-semibold rounded transition-all ${
                        depth === d ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Board</span>
                  {[
                    { value: 'auto', label: 'Auto' },
                    { value: 'front', label: 'Front' },
                    { value: 'back', label: 'Back' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => toggleOrientation(opt.value)}
                      disabled={isLoading}
                      className={`px-2 py-1 text-xs font-semibold rounded transition-all ${
                        orientation === opt.value ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {opt.label}
                    </button>
                    ))}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-xs text-slate-400">Turn</span>
                  {[
                    { value: 'w', label: 'White' },
                    { value: 'b', label: 'Black' },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setTurn(opt.value)}
                      disabled={isLoading}
                      className={`px-2 py-1 text-xs font-semibold rounded transition-all ${
                        turn === opt.value ? 'bg-emerald-500 text-white' : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                      } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl">
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h2 className="text-sm font-semibold text-white">Upload Image</h2>
            </div>
            <UploadImage
              onResult={handleResult}
              setStatus={setStatus}
              setIsLoading={setIsLoading}
              abortControllerRef={abortControllerRef}
              orientation={orientation}
              turn={turn}
              depth={depth}
            />
          </section>

          {(overlayImage || fen) ? (
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2 min-h-0">
              {overlayImage && (
                <section className="rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl flex flex-col min-h-0">
                  <div className="flex items-center gap-2 mb-2 flex-shrink-0">
                    <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <h2 className="text-sm font-semibold text-white">Board</h2>
                  </div>
                  <div className="flex-1 rounded overflow-hidden border border-slate-700 bg-black min-h-0 flex items-center justify-center">
                    <img
                      src={`data:image/png;base64,${overlayImage}`}
                      alt="Analyzed board"
                      className="max-w-full max-h-full object-contain"
                    />
                  </div>
                </section>
              )}

              <section className="rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl overflow-y-auto min-h-0">
                <BoardPreview
                  fen={fen}
                  bestMove={bestMoveText}
                  confidence={confidence}
                  evaluationText={evaluationText}
                  score={score}
                  pv={pv}
                  error={error}
                  fenWarnings={fenWarnings}
                />
              </section>
            </div>
          ) : (
            <div className="flex-1"></div>
          )}

          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl">
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              <h2 className="text-sm font-semibold text-white">Controls</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                onClick={handleManualBestMove}
                disabled={isLoading || !fen}
                className="col-span-2 sm:col-span-1 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <span>Analyze</span>
              </button>

              <button
                onClick={downloadOverlay}
                disabled={!overlayImage}
                className="rounded-lg bg-slate-700 px-2 py-2 text-xs font-semibold text-white hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <span>Download</span>
              </button>

              <div className="rounded-lg bg-slate-700/50 px-2 py-2 text-xs font-semibold text-white overflow-y-auto max-h-20">
                <span className="text-slate-400 block mb-1">Moves</span>
                <span className="text-slate-200">
                  {moveHistory.length ? moveHistory.join(' ') : 'No moves yet'}
                </span>
              </div>

              <button
                onClick={handleClearContext}
                disabled={isLoading}
                className="rounded-lg bg-gradient-to-r from-red-500 to-red-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <span>Clear</span>
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
