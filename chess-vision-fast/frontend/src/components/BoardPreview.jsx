import React from 'react'

function winPercent(cp, mate) {
  if (mate != null) return mate > 0 ? 100 : 0
  if (cp == null) return 50
  return Math.round(100 / (1 + Math.pow(10, -cp / 400)))
}

export default function BoardPreview({
  fen,
  bestMove,
  confidence,
  evaluationText,
  score,
  pv,
  error,
}) {
  const whitePct = score ? winPercent(score.cp, score.mate) : null
  return (
    <div className="space-y-2">
      {error && (
        <div className="rounded border border-red-500/30 bg-red-500/10 p-2">
          <p className="text-xs font-semibold text-red-400 mb-1">Error</p>
          <p className="text-xs text-red-300">{error}</p>
        </div>
      )}

      {score && (
        <div className="rounded border border-slate-700 bg-slate-900/50 p-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
            Evaluation
          </p>
          <div className="flex h-3 w-full overflow-hidden rounded bg-slate-700">
            <div
              className="bg-emerald-500"
              style={{ width: `${whitePct}%` }}
            ></div>
          </div>
          <p className="mt-1 text-xs text-slate-200">
            {score.mate != null
              ? `Mate in ${Math.abs(score.mate)}`
              : `${score.cp == null ? 'n/a' : (score.cp / 100).toFixed(1)}`}
            {evaluationText && <span className="text-slate-400"> — {evaluationText}</span>}
          </p>
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

          {pv && pv.length > 0 && (
            <div className="rounded border border-slate-700/50 bg-slate-900/30 p-2">
              <p className="text-xs font-semibold text-slate-400 mb-0.5">Line</p>
              <p className="text-xs text-slate-200">{pv.join(' ')}</p>
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
