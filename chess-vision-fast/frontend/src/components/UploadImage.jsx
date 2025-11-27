import React, { useRef, useState, useEffect } from 'react'
import { detectAndMove } from '../services/api'

export default function UploadImage({ onResult, setStatus, setIsLoading, abortControllerRef }) {
  const input = useRef(null)
  const dropZoneRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  // Procesar archivo (compartido entre upload, drop y paste)
  async function processFile(file) {
    if (!file || !file.type.startsWith('image/')) {
      setStatus('Archivo no es una imagen válida')
      return
    }
    
    // Cancelar operación anterior si existe
    if (abortControllerRef?.current) {
      abortControllerRef.current.abort()
    }
    
    // Crear nuevo AbortController
    abortControllerRef.current = new AbortController()
    
    if (setIsLoading) setIsLoading(true)
    setStatus('Analizando imagen con Gemini...')
    
    try {
      const data = await detectAndMove(file, abortControllerRef.current.signal)
      onResult(data)
      if (!data.error) {
        setStatus('Análisis completado')
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setStatus('Análisis cancelado')
      } else {
        console.error(error)
        const errorMsg = error.message || 'Error procesando imagen'
        setStatus(`Error: ${errorMsg}`)
        onResult({ error: errorMsg })
      }
    } finally {
      if (setIsLoading) setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  // Handler para input file
  async function handleUpload(event) {
    const file = event.target.files?.[0]
    if (!file) return
    await processFile(file)
    if (input.current) input.current.value = ''
  }

  // Handlers para drag & drop
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
    if (file) {
      await processFile(file)
    }
  }

  // Handler para Ctrl+V (paste)
  useEffect(() => {
    async function handlePaste(e) {
      const items = e.clipboardData?.items
      if (!items) return

      for (const item of items) {
        if (item.type.startsWith('image/')) {
          e.preventDefault()
          const file = item.getAsFile()
          if (file) {
            await processFile(file)
          }
          break
        }
      }
    }

    document.addEventListener('paste', handlePaste)
    return () => document.removeEventListener('paste', handlePaste)
  }, [])

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
            Arrastra una imagen aqui o{' '}
            <label className="cursor-pointer text-emerald-400 hover:text-emerald-300">
              busca en tu equipo
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
            Tambien puedes pegar con Ctrl+V
          </p>
        </div>
      </div>
    </div>
  )
}
