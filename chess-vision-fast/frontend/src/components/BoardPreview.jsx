import React from 'react'

export default function BoardPreview({ 
  overlayImage, 
  fen, 
  bestMove, 
  confidence,
  explanation,
  positionAnalysis,
  strategicNotes,
  error
}) {
  return (
    <div className="space-y-2">
      {error && (
        <div className="rounded border border-red-500/30 bg-red-500/10 p-2">
          <p className="text-xs font-semibold text-red-400 mb-1">Error</p>
          <p className="text-xs text-red-300">{error}</p>
        </div>
      )}

      {fen && (
        <div className="rounded border border-slate-700 bg-slate-900/50 p-2">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">FEN</p>
            {confidence !== null && (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-1.5 py-0.5 text-xs font-semibold text-emerald-400">
                <div className="h-1 w-1 rounded-full bg-emerald-400"></div>
                {confidence?.toFixed(2) ?? 'n/a'}
              </span>
            )}
          </div>
          <p className="text-xs font-mono text-slate-200 break-all">{fen}</p>
        </div>
      )}

      {bestMove && (
        <div className="space-y-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-2 backdrop-blur-sm">
          <div className="flex items-center gap-1.5">
            <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <p className="text-xs font-semibold text-emerald-400">Best Move</p>
          </div>
          <p className="text-base font-bold text-white">{bestMove}</p>
          
          {explanation && (
            <div className="rounded border border-slate-700/50 bg-slate-900/30 p-2">
              <p className="text-xs font-semibold text-slate-400 mb-0.5">Explanation</p>
              <p className="text-xs text-slate-200 leading-relaxed">{explanation}</p>
            </div>
          )}
          
          {positionAnalysis && (
            <div className="rounded border border-slate-700/50 bg-slate-900/30 p-2">
              <p className="text-xs font-semibold text-slate-400 mb-0.5">Analysis</p>
              <p className="text-xs text-slate-200 leading-relaxed">{positionAnalysis}</p>
            </div>
          )}
          
          {strategicNotes && (
            <div className="rounded border border-slate-700/50 bg-slate-900/30 p-2">
              <p className="text-xs font-semibold text-slate-400 mb-0.5">Strategy</p>
              <p className="text-xs text-slate-200 leading-relaxed">{strategicNotes}</p>
            </div>
          )}
        </div>
      )}

      {!bestMove && fen && !error && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-2 text-center">
          <p className="text-xs text-amber-400">
            Click "Analyze" to get the best move
          </p>
        </div>
      )}
    </div>
  )
}
