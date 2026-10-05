import React, { useState } from 'react'
import { parseImport } from '../lib/chess'

const PRESETS = [
  {
    name: 'After 1. e4 (Screenshot Demo)',
    fen: 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1',
  },
  {
    name: 'Starting Position',
    fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
  },
  {
    name: 'Sicilian Defense',
    fen: 'rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2',
  },
  {
    name: 'Queen\'s Gambit',
    fen: 'rnbqkbnr/ppp1pppp/8/3p4/2PP4/8/PP2PPPP/RNBQKBNR b KQkq c3 0 2',
  },
]

export default function ImportModal({ isOpen, onClose, onImport }) {
  const [inputText, setInputText] = useState('')
  const [error, setError] = useState(null)

  if (!isOpen) return null

  const handleApply = () => {
    try {
      const parsed = parseImport(inputText)
      setError(null)
      onImport(parsed)
      onClose()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSelectPreset = (fen) => {
    setInputText(fen)
    setError(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <h3 className="text-base font-bold text-white">Import FEN or PGN</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 space-y-4">
          <div>
            <label htmlFor="fen-input" className="block text-xs font-semibold text-slate-300 mb-1">
              FEN / PGN string:
            </label>
            <textarea
              id="fen-input"
              rows={3}
              value={inputText}
              onChange={(e) => {
                setInputText(e.target.value)
                setError(null)
              }}
              placeholder="e.g. rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-xs font-mono text-emerald-300 placeholder-slate-600 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            {error && <p role="alert" className="mt-1 text-xs text-red-400">{error}</p>}
          </div>

          <div>
            <span className="block text-xs font-semibold text-slate-400 mb-1.5">
              Or choose a preset position:
            </span>
            <div className="grid grid-cols-2 gap-2">
              {PRESETS.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => handleSelectPreset(preset.fen)}
                  className="px-2.5 py-1.5 rounded-lg border border-slate-800 bg-slate-800/60 hover:bg-slate-800 hover:border-emerald-500/40 text-left text-xs text-slate-300 transition-all"
                >
                  <p className="font-semibold text-white truncate">{preset.name}</p>
                  <p className="text-[10px] text-slate-400 font-mono truncate">{preset.fen}</p>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-end gap-2 border-t border-slate-800 pt-3">
          <button
            onClick={onClose}
            className="rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-400 hover:bg-slate-800 hover:text-white transition-all"
          >
            Cancel
          </button>
          <button
            onClick={handleApply}
            className="rounded-lg bg-emerald-500 hover:bg-emerald-600 px-4 py-1.5 text-xs font-bold text-white shadow-lg transition-all"
          >
            Load Position
          </button>
        </div>
      </div>
    </div>
  )
}
