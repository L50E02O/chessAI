import React from 'react'

export default function BoardPreview({ 
  overlayImage, 
  fen, 
  bestMove, 
  confidence,
  explanation,
  positionAnalysis,
  strategicNotes 
}) {
  return (
    <div className="space-y-2 rounded border border-slate-800 bg-slate-900 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">FEN</p>
        <span className="text-xs text-emerald-400">Confianza {confidence?.toFixed(2) ?? 'n/a'}</span>
      </div>
      <p className="text-xs font-mono text-slate-200 break-all">{fen || 'Sin detección'}</p>
      <div className="h-64 w-full overflow-hidden rounded border border-slate-800 bg-black">
        {overlayImage ? (
          <img
            src={`data:image/png;base64,${overlayImage}`}
            alt="Vista del tablero"
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Sube una imagen o inicia la cámara
          </div>
        )}
      </div>
      {bestMove && (
        <div className="space-y-2 rounded border border-slate-700 bg-slate-800 p-3">
          <p className="text-sm font-semibold text-emerald-400">
            Mejor jugada: <span className="text-white">{bestMove}</span>
          </p>
          {explanation && (
            <p className="text-xs text-slate-300">{explanation}</p>
          )}
          {positionAnalysis && (
            <div className="mt-2 border-t border-slate-700 pt-2">
              <p className="text-xs font-semibold text-slate-400">Análisis de posición:</p>
              <p className="text-xs text-slate-300">{positionAnalysis}</p>
            </div>
          )}
          {strategicNotes && (
            <div className="mt-2 border-t border-slate-700 pt-2">
              <p className="text-xs font-semibold text-slate-400">Notas estratégicas:</p>
              <p className="text-xs text-slate-300">{strategicNotes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
