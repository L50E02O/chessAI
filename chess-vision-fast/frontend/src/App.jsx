import React, { useState } from 'react'
import CameraCapture from './components/CameraCapture'
import UploadImage from './components/UploadImage'
import BoardPreview from './components/BoardPreview'
import { bestMove, clearContext, getRetrospective } from './services/api'

export default function App() {
  const [status, setStatus] = useState('Listo')
  const [overlayImage, setOverlayImage] = useState(null)
  const [fen, setFen] = useState('')
  const [bestMoveText, setBestMoveText] = useState('')
  const [explanation, setExplanation] = useState('')
  const [positionAnalysis, setPositionAnalysis] = useState('')
  const [strategicNotes, setStrategicNotes] = useState('')
  const [confidence, setConfidence] = useState(null)
  const [retrospective, setRetrospective] = useState(null)
  const [showRetrospective, setShowRetrospective] = useState(false)

  const handleResult = (data) => {
    setFen(data.fen)
    setOverlayImage(data.overlay_image_base64 || data.board_image_base64)
    setBestMoveText(data.best_move || data.uci || '')
    setExplanation(data.explanation || '')
    setPositionAnalysis(data.position_analysis || '')
    setStrategicNotes(data.strategic_notes || '')
    setConfidence(data.confidence)
    setStatus('Detección actualizada')
  }

  const handleManualBestMove = async () => {
    if (!fen) {
      setStatus('No hay FEN disponible')
      return
    }
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
    }
  }

  const handleClearContext = async () => {
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
    }
  }

  const handleGetRetrospective = async () => {
    setStatus('Generando retrospectiva...')
    try {
      const response = await getRetrospective()
      setRetrospective(response.retrospective)
      setShowRetrospective(true)
      setStatus('Retrospectiva generada')
    } catch (error) {
      console.error(error)
      setStatus('Error al obtener retrospectiva')
    }
  }

  const downloadOverlay = () => {
    if (!overlayImage) return
    const link = document.createElement('a')
    link.href = `data:image/png;base64,${overlayImage}`
    link.download = 'overlay.png'
    link.click()
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6">
      <header className="mx-auto max-w-5xl space-y-2 text-center">
        <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Chess Vision Fast</p>
        <h1 className="text-3xl font-semibold text-white">Análisis de Ajedrez con Gemini AI</h1>
        <p className="text-slate-400">
          Sube una foto o usa la cámara para detectar las piezas y obtener análisis de un Gran Maestro virtual.
        </p>
      </header>

      <main className="mx-auto mt-8 grid max-w-5xl gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2 space-y-4">
          <div className="rounded border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Cámara</h2>
              <span className="text-xs text-slate-400">{status}</span>
            </div>
            <CameraCapture onResult={handleResult} setStatus={setStatus} />
          </div>
          <UploadImage onResult={handleResult} setStatus={setStatus} />
        </section>

        <section className="space-y-4">
          <BoardPreview 
            overlayImage={overlayImage} 
            fen={fen} 
            bestMove={bestMoveText}
            confidence={confidence}
            explanation={explanation}
            positionAnalysis={positionAnalysis}
            strategicNotes={strategicNotes}
          />
          <div className="space-y-2 rounded border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Controles</h2>
              <button
                onClick={downloadOverlay}
                className="rounded bg-slate-700 px-3 py-1 text-xs font-semibold text-white"
              >
                Descargar overlay
              </button>
            </div>
            <div className="space-y-2">
              <button
                onClick={handleManualBestMove}
                className="w-full rounded bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-600"
              >
                Analizar posición
              </button>
              <button
                onClick={handleClearContext}
                className="w-full rounded bg-red-500 px-4 py-2 text-sm font-semibold text-white hover:bg-red-600"
              >
                Limpiar contexto
              </button>
              <button
                onClick={handleGetRetrospective}
                className="w-full rounded bg-blue-500 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600"
              >
                Ver retrospectiva
              </button>
            </div>
            {showRetrospective && retrospective && (
              <div className="mt-4 rounded border border-slate-700 bg-slate-800 p-3">
                <h3 className="mb-2 text-sm font-semibold text-blue-400">Retrospectiva de la partida</h3>
                <p className="text-xs text-slate-300 whitespace-pre-wrap">{retrospective}</p>
                <button
                  onClick={() => setShowRetrospective(false)}
                  className="mt-2 text-xs text-slate-400 hover:text-slate-200"
                >
                  Ocultar
                </button>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}
