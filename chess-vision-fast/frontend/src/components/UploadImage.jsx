import React, { useRef, useState, useEffect } from 'react'
import { detectAndMove } from '../services/api'

export default function UploadImage({ onResult, setStatus, setIsLoading, abortControllerRef, orientation, turn, depth }) {
  const input = useRef(null)
  const dropZoneRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  async function processFile(file) {
    if (!file || !file.type.startsWith('image/')) {
      setStatus('File is not a valid image')
      return
    }

    if (abortControllerRef?.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()

    if (setIsLoading) setIsLoading(true)
    setStatus('Analyzing image with Stockfish...')

    try {
      const data = await detectAndMove(file, abortControllerRef.current.signal, orientation, turn, depth)
      onResult(data)
      if (!data.error) {
        setStatus('Analysis completed')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Analysis cancelled')
      } else {
        console.error(error)
        const errorMsg = error.message || 'Error processing image'
        setStatus(`Error: ${errorMsg}`)
        onResult({ error: errorMsg })
      }
    } finally {
      if (setIsLoading) setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  function handleUpload(event) {
    const file = event.target.files?.[0]
    if (!file) return
    processFile(file)
    if (input.current) input.current.value = ''
  }

  function handleDragOver(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  function handleDragLeave(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  async function handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) await processFile(file)
  }

  useEffect(() => {
    async function handlePaste(e) {
      const items = e.clipboardData?.items
      if (!items) return
      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const file = item.getAsFile()
          if (file) await processFile(file)
          break
        }
      }
    }
    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [orientation, turn, depth])

  return (
    <div
      ref={dropZoneRef}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`rounded border-2 border-dashed p-3 text-center transition-colors ${
        isDragging
          ? 'border-emerald-500 bg-emerald-500/10'
          : 'border-slate-700 bg-slate-900 hover:border-slate-600'
      }`}
    >
      <div className="space-y-2">
        <div className="text-slate-400">
          <svg
            className="mx-auto h-8 w-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-300">
            Drag an image here or{' '}
            <label className="cursor-pointer text-emerald-400 hover:text-emerald-300">
              browse your device
              <input
                ref={input}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleUpload}
                className="hidden"
              />
            </label>
          </p>
          <p className="mt-0.5 text-xs text-slate-500">
            You can also paste with Ctrl+V
          </p>
        </div>
      </div>
    </div>
  )
}
