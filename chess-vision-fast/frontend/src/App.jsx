import React, { useMemo, useState } from 'react'
import CameraCapture from './components/CameraCapture'
import UploadImage from './components/UploadImage'
import BoardPreview from './components/BoardPreview'
import Controls from './components/Controls'
import { detectAndMove, bestMove } from './services/api'

export default function App() {
  const [status, setStatus] = useState('Listo')
  const [overlayImage, setOverlayImage] = useState(null)
  const [fen, setFen] = useState('')
  const [bestMoveText, setBestMoveText] = useState('')
  const [confidence, setConfidence] = useState(null)
  const [detector, setDetector] = useState('lichess')
  const [depth, setDepth] = useState(12)
  const [timeMs, setTimeMs] = useState(800)

  const handleResult = (data) => {
    setFen(data.fen)
    setOverlayImage(data.overlay_image_base64 || data.board_image_base64)
    setBestMoveText(data.best_move || data.uci || '')
    setConfidence(data.confidence)
    setStatus('Detección actualizada')
  }

  const handleManualBestMove = async () => {
    if (!fen) {
      setStatus('No hay FEN disponible')
      return
    }
    setStatus('Calculando mejor jugada...')
    try {
      const response = await bestMove(fen, { depth, time_ms: timeMs })
      setBestMoveText(response.best_move)
      setStatus('Mejor jugada actualizada')
    } catch (error) {
      console.error(error)
      setStatus('Error al calcular la jugada')
    }
  }

  const downloadOverlay = () => {
    if (!overlayImage) return
    const link = document.createElement('a')
    link.href = data:image/png;base64,
    link.download = 'overlay.png'
    link.click()
  }

  const cameraProps = useMemo(
    () => ({ detector }),
    [detector],
  )

  return (
    <div className= min-h-screen bg-slate-950 px-4 py-6>
      <header className=mx-auto max-w-5xl space-y-2 text-center>
        <p className=text-sm uppercase tracking-[0.3em] text-slate-500>Chess Vision Fast</p>
        <h1 className=text-3xl font-semibold text-white>Analiza tu tablero físico en segundos</h1>
        <p className=text-slate-400>
          Sube una foto o usa la cámara para detectar las piezas, generar FEN y pedir la mejor jugada desde Stockfish.
        </p>
      </header>

      <main className=mx-auto mt-8 grid max-w-5xl gap-6 lg:grid-cols-3>
        <section className=lg:col-span-2 space-y-4>
          <div className=rounded border border-slate-800 bg-slate-900 p-4>
            <div className=flex items-center justify-between>
              <h2 className=text-lg font-semibold text-white>Cámara</h2>
              <span className=text-xs text-slate-400>{status}</span>
            </div>
            <CameraCapture onResult={handleResult} setStatus={setStatus} {...cameraProps} />
          </div>
          <UploadImage onResult={handleResult} setStatus={setStatus} detector={detector} />
        </section>

        <section className=space-y-4>
          <BoardPreview overlayImage={overlayImage} fen={fen} bestMove={bestMoveText} confidence={confidence} />
          <div className=space-y-2 rounded border border-slate-800 bg-slate-900 p-4>
            <div className=flex items-center justify-between>
              <h2 className=text-lg font-semibold text-white>Ajustes</h2>
              <button
                onClick={downloadOverlay}
                className=rounded bg-slate-700 px-3 py-1 text-xs font-semibold text-white
              >
                Descargar overlay
              </button>
            </div>
            <Controls
              depth={depth}
              setDepth={setDepth}
              timeMs={timeMs}
              setTimeMs={setTimeMs}
              detector={detector}
              setDetector={setDetector}
            />
            <button
              onClick={handleManualBestMove}
              className=w-full rounded bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950
            >
              Calcular mejor jugada
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}
