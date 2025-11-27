import React, { useState } from 'react'
import UploadImage from './components/UploadImage'
import BoardPreview from './components/BoardPreview'
import { bestMove, clearContext, getRetrospective } from './services/api'

export default function App() {
  const [status, setStatus] = useState('Listo para analizar')
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

  const handleResult = (data) => {
    setFen(data.fen)
    setOverlayImage(data.overlay_image_base64 || data.board_image_base64)
    setBestMoveText(data.best_move || data.uci || '')
    setExplanation(data.explanation || '')
    setPositionAnalysis(data.position_analysis || '')
    setStrategicNotes(data.strategic_notes || '')
    setConfidence(data.confidence)
    setStatus('Análisis completado')
    setIsLoading(false)
  }

  const handleManualBestMove = async () => {
    if (!fen) {
      setStatus('Primero sube una imagen del tablero')
      return
    }
    setIsLoading(true)
    setStatus('Analizando con Gemini GM...')
    try {
      const response = await bestMove(fen)
      setBestMoveText(response.best_move || response.uci || '')
      setExplanation(response.explanation || '')
      setPositionAnalysis(response.position_analysis || '')
      setStrategicNotes(response.strategic_notes || '')
      setStatus('Análisis completado')
    } catch (error) {
      console.error(error)
      setStatus('Error al analizar la posición')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearContext = async () => {
    setIsLoading(true)
    setStatus('Limpiando contexto...')
    try {
      await clearContext()
      setFen('')
      setBestMoveText('')
      setExplanation('')
      setPositionAnalysis('')
      setStrategicNotes('')
      setOverlayImage(null)
      setRetrospective(null)
      setShowRetrospective(false)
      setStatus('Contexto limpiado - Listo para nueva partida')
    } catch (error) {
      console.error(error)
      setStatus('Error al limpiar contexto')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGetRetrospective = async () => {
    setIsLoading(true)
    setStatus('Generando retrospectiva...')
    try {
      const response = await getRetrospective()
      setRetrospective(response.retrospective)
      setShowRetrospective(true)
      setStatus('Retrospectiva generada')
    } catch (error) {
      console.error(error)
      setStatus('Error al obtener retrospectiva')
    } finally {
      setIsLoading(false)
    }
  }

  const downloadOverlay = () => {
    if (!overlayImage) return
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${overlayImage}`
    link.download = 'tablero-analizado.png'
    link.click()
  }

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Header - Compacto */}
      <header className="flex-shrink-0 px-4 py-2 text-center border-b border-slate-700/50">
        <div className="flex items-center justify-center gap-3">
          <div className="inline-block rounded-full bg-emerald-500/20 px-2 py-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Chess Vision Fast</p>
          </div>
          <h1 className="text-lg sm:text-xl font-bold text-white">
            Analisis con{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
              Gemini AI
            </span>
          </h1>
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <div className={`h-1.5 w-1.5 rounded-full ${isLoading ? 'bg-yellow-500 animate-pulse' : 'bg-emerald-500'}`}></div>
            <span className="hidden sm:inline">{status}</span>
          </div>
        </div>
      </header>

      {/* Main Content - Flex para ocupar espacio restante */}
      <main className="flex-1 overflow-hidden px-4 py-2">
        <div className="h-full flex flex-col gap-2 max-w-7xl mx-auto">
          {/* Upload Section - Compacto */}
          <section className="flex-shrink-0 rounded-lg border border-slate-700 bg-slate-800/50 backdrop-blur-sm p-3 shadow-xl">
            <div className="flex items-center gap-2 mb-2">
              <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h2 className="text-sm font-semibold text-white">Subir Imagen</h2>
            </div>
            <UploadImage onResult={handleResult} setStatus={setStatus} setIsLoading={setIsLoading} />
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
                    <h2 className="text-sm font-semibold text-white">Tablero</h2>
                  </div>
                  <div className="flex-1 rounded overflow-hidden border border-slate-700 bg-black min-h-0 flex items-center justify-center">
                    <img
                      src={`data:image/png;base64,${overlayImage}`}
                      alt="Tablero analizado"
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
              <h2 className="text-sm font-semibold text-white">Controles</h2>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                onClick={handleManualBestMove}
                disabled={isLoading || !fen}
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
                <span>Analizar</span>
              </button>
              
              <button
                onClick={downloadOverlay}
                disabled={!overlayImage}
                className="rounded-lg bg-slate-700 px-2 py-2 text-xs font-semibold text-white hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span>Descargar</span>
              </button>
              
              <button
                onClick={handleGetRetrospective}
                disabled={isLoading || !fen}
                className="rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>Retrospectiva</span>
              </button>
              
              <button
                onClick={handleClearContext}
                disabled={isLoading}
                className="rounded-lg bg-gradient-to-r from-red-500 to-red-600 px-2 py-2 text-xs font-semibold text-white shadow-lg hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-1.5"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span>Limpiar</span>
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
                    Retrospectiva
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
