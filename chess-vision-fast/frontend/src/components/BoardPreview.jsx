import React from 'react'

export default function BoardPreview({ overlayImage, fen, bestMove, confidence }) {
  return (
    <div className= space-y-2 rounded border border-slate-800 bg-slate-900 p-4>
      <div className=flex items-center justify-between>
        <p className=text-sm text-slate-400>FEN</p>
        <span className=text-xs text-emerald-400>Confianza {confidence?.toFixed(2) ?? 'n/a'}</span>
      </div>
      <p className=text-xs font-mono text-slate-200>{fen || 'Sin detección'}</p>
      <div className=h-64 w-full overflow-hidden rounded border border-slate-800 bg-black>
        {overlayImage ? (
          <img
            src={data:image/png;base64,}
            alt=Vista del tablero
            className=h-full w-full object-contain
          />
        ) : (
          <div className=flex h-full items-center justify-center text-sm text-slate-500>
            Sube una imagen o inicia la cámara
          </div>
        )}
      </div>
      <p className=text-sm text-slate-200>Mejor jugada: {bestMove || 'esperando'}</p>
    </div>
  )
}
