import React, { useState, useRef, useEffect } from 'react'
import UploadImage from './components/UploadImage'
import BoardPreview from './components/BoardPreview'
import { bestMove, clearContext, getRetrospective, changeModel, getCurrentModel, detectAndMove } from './services/api'

const AVAILABLE_MODELS = [
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash', description: 'Fast and precise (15 RPM)' },
  { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', description: 'Balanced (10 RPM)' },
  { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro', description: 'More powerful (2 RPM)' },
]

export default function App() {
  const [status, setStatus] = useState('Ready to analyze')
  const [overlayImage, setOverlayImage] = useState(null)
  const [fen, setFen] = useState('')
  const [bestMoveText, setBestMoveText] = useState('')
  const [explanation, setExplanation] = useState('')
  const [positionAnalysis, setPositionAnalysis] = useState('')
  const [strategicNotes, setStrategicNotes] = useState('')
  const [confidence, setConfidence] = useState(null)
  const [retrospective, setRetrospective] = useState(null)
  const [showRetrospective, setShowRetrospective] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedModel, setSelectedModel] = useState('gemini-2.0-flash')
  const [modelChanging, setModelChanging] = useState(false)
  
  // AbortController to cancel operations
  const abortControllerRef = useRef(null)

  // Load current model on startup
  useEffect(() => {
    getCurrentModel()
      .then(data => {
        if (data.model) {
          setSelectedModel(data.model)
        }
      })
      .catch(err => console.error('Error loading model:', err))
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

  const handleModelChange = async (newModel) => {
    if (newModel === selectedModel) return
    
    setModelChanging(true)
    setStatus('Changing model...')
    try {
      await changeModel(newModel)
      setSelectedModel(newModel)
      setStatus('Model changed successfully')
      // Clear context when changing model
      await clearContext()
    } catch (error) {
      console.error(error)
      setError(`Error changing model: ${error.message}`)
      setStatus('Error changing model')
    } finally {
      setModelChanging(false)
    }
  }

  const handleResult = (data) => {
    setFen(data.fen || '')
    setOverlayImage(data.overlay_image_base64 || data.board_image_base64)
    setBestMoveText(data.best_move || data.uci || '')
    setExplanation(data.explanation || '')
    setPositionAnalysis(data.position_analysis || '')
    setStrategicNotes(data.strategic_notes || '')
    setConfidence(data.confidence)
    
    if (data.error) {
      setError(data.error)
      setStatus(`Error: ${data.error}`)
    } else {
      setError(null)
      setStatus('Analysis completed')
    }
    setIsLoading(false)
  }

  const handleManualBestMove = async () => {
    if (!fen) {
      setStatus('First upload a board image')
      setError('No FEN available')
      return
    }
    
    // Cancel previous operation if exists
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)
    setStatus(`Analyzing with ${selectedModel}...`)
    
    try {
      const response = await bestMove(fen, abortControllerRef.current.signal, selectedModel)
      setBestMoveText(response.best_move || response.uci || '')
      setExplanation(response.explanation || '')
      setPositionAnalysis(response.position_analysis || '')
      setStrategicNotes(response.strategic_notes || '')
      
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
      setExplanation('')
      setPositionAnalysis('')
      setStrategicNotes('')
      setOverlayImage(null)
      setRetrospective(null)
      setShowRetrospective(false)
      setError(null)
      setStatus('Context cleared - Ready for new game')
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Operation cancelled')
        setError(null)
      } else {
        console.error(error)
        const errorMsg = error.message || 'Error clearing context'
        setError(errorMsg)
        setStatus(`Error: ${errorMsg}`)
      }
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  const handleGetRetrospective = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    abortControllerRef.current = new AbortController()
    setIsLoading(true)
    setError(null)
    setStatus('Generating retrospective...')
    
    try {
      const response = await getRetrospective(abortControllerRef.current.signal)
      setRetrospective(response.retrospective)
      setShowRetrospective(true)
      setError(null)
      setStatus('Retrospective generated')
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Operation cancelled')
        setError(null)
      } else {
        console.error(error)
        const errorMsg = error.message || 'Error getting retrospective'
        setError(errorMsg)
        setStatus(`Error: ${errorMsg}`)
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

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Header - Compacto */}
      <header className="flex-shrink-0 px-4 py-2 text-center border-b border-slate-700/50">
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <div className="inline-block rounded-full bg-emerald-500/20 px-2 py-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Chess Vision Fast</p>
          </div>
          <h1 className="text-lg sm:text-xl font-bold text-white">
            Analysis with{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
              Gemini AI
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

      {/* Main Content - Flex para ocupar espacio restante */}
      <main className="flex-1 overflow-hidden px-4 py-2">
        <div className="h-full flex flex-col gap-2 max-w-7xl mx-auto">
          {/* Model Selector */}
          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-2 shadow-xl">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span className="text-xs font-semibold text-white">Gemini Model</span>
              </div>
              <div className="flex gap-1">
                {AVAILABLE_MODELS.map((model) => (
                  <button
                    key={model.value}
                    onClick={() => handleModelChange(model.value)}
                    disabled={modelChanging || isLoading}
                    className={`px-2 py-1 text-xs font-semibold rounded transition-all ${
                      selectedModel === model.value
                        ? 'bg-emerald-500 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                    title={model.description}
                  >
                    {model.label.split(' ')[1]}
                  </button>
                ))}
              </div>
            </div>
            <div className="mt-1 text-xs text-slate-400 text-center">
              {AVAILABLE_MODELS.find(m => m.value === selectedModel)?.description}
            </div>
          </section>

          {/* Upload Section - Compacto */}
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
              selectedModel={selectedModel}
            />
          </section>

          {/* Results Grid - Ocupa espacio restante */}
          {(overlayImage || fen) ? (
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2 min-h-0">
              {/* Board Image */}
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

              {/* Analysis Panel */}
              <section className="rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl overflow-y-auto min-h-0">
                <BoardPreview 
                  overlayImage={overlayImage} 
                  fen={fen} 
                  bestMove={bestMoveText}
                  confidence={confidence}
                  explanation={explanation}
                  positionAnalysis={positionAnalysis}
                  strategicNotes={strategicNotes}
                  error={error}
                />
              </section>
            </div>
          ) : (
            <div className="flex-1"></div>
          )}

          {/* Controls - Compacto */}
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
                disabled={isLoading || !fen || modelChanging}
                className="col-span-2 sm:col-span-1 rounded-lg bg-gradient-to-r from-emerald-500 to-emerald-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-emerald-600 hover:to-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                {isLoading ? (
                  <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                )}
                <span>Analyze</span>
              </button>
              
              <button
                onClick={downloadOverlay}
                disabled={!overlayImage}
                className="rounded-lg bg-slate-700 px-2 py-2 text-xs font-semibold text-white hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Download</span>
              </button>
              
              <button
                onClick={handleGetRetrospective}
                disabled={isLoading || !fen || modelChanging}
                className="rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>Retrospective</span>
              </button>
              
              <button
                onClick={handleClearContext}
                disabled={isLoading || modelChanging}
                className="rounded-lg bg-gradient-to-r from-red-500 to-red-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span>Clear</span>
              </button>
            </div>
            
            {/* Retrospective Modal - Compacto */}
            {showRetrospective && retrospective && (
              <div className="mt-2 rounded-lg border border-blue-500/30 bg-blue-500/10 p-2 backdrop-blur-sm max-h-32 overflow-y-auto">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-xs font-semibold text-blue-400 flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Retrospective
                  </h3>
                  <button
                    onClick={() => setShowRetrospective(false)}
                    className="text-blue-400 hover:text-blue-300 transition-colors p-0.5"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{retrospective}</p>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}
