import React, { useRef } from 'react'
import { detectAndMove } from '../services/api'

export default function UploadImage({ onResult, setStatus, detector }) {
  const input = useRef(null)

  async function handleUpload(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setStatus('Analizando imagen...')
    try {
      const data = await detectAndMove(file, detector)
      onResult(data)
      setStatus('Imagen procesada')
    } catch (error) {
      console.error(error)
      setStatus('Error procesando imagen')
    } finally {
      if (input.current) input.current.value = ''
    }
  }

  return (
    <label className= block>
      <span className=mb-2 block text-sm font-semibold text-slate-300>Subir imagen</span>
      <input
        ref={input}
        type=file
        accept=image/png,image/jpeg
        onChange={handleUpload}
        className=block w-full rounded border border-slate-800 bg-slate-900 px-3 py-2 text-sm text-white
      />
    </label>
  )
}
