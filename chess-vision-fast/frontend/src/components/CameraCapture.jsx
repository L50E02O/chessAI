import React, { useEffect, useRef, useState } from 'react'
import { openStream } from '../services/api'

export default function CameraCapture({ onResult, setStatus, detector }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const socketRef = useRef(null)
  const [isRunning, setIsRunning] = useState(false)
  const runningRef = useRef(false)

  useEffect(() => {
    return () => {
      stop()
    }
  }, [])

  function stop() {
    runningRef.current = false
    setIsRunning(false)
    if (socketRef.current) {
      socketRef.current.close()
      socketRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }

  async function start() {
    setStatus('Iniciando webcam...')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      const socket = openStream(
        async (frame) => {
          onResult(frame)
          setStatus('Frame recibido')
        },
        (error) => {
          console.error('WebSocket error', error)
          setStatus('Error websocket')
        },
        detector,
      )
        onResult(frame)
        setStatus('Frame recibido')
      }, (error) => {
        console.error('WebSocket error', error)
        setStatus('Error websocket')
      })
      socketRef.current = socket
    runningRef.current = true
    setIsRunning(true)
    captureLoop()
    } catch (error) {
      console.error(error)
      setStatus('No se pudo acceder a la cámara')
    }
  }

  function captureLoop() {
    if (!runningRef.current || !videoRef.current || !canvasRef.current || !socketRef.current) return
    const video = videoRef.current
    const canvas = canvasRef.current
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const context = canvas.getContext('2d')
    context.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/png')
    socketRef.current.sendFrame(dataUrl)
    setTimeout(captureLoop, 600)
  }

  return (
    <div className= space-y-2>
      <div className=relative h-64 w-full overflow-hidden rounded border border-slate-800 bg-slate-900>
        <video ref={videoRef} autoPlay playsInline muted className=h-full w-full object-cover />
        <canvas ref={canvasRef} className=hidden />
      </div>
      <div className=flex gap-2>
        <button
          onClick={start}
          disabled={isRunning}
          className=flex-1 rounded bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950
        >
          Iniciar cámara
        </button>
        <button
          onClick={stop}
          disabled={!isRunning}
          className=flex-1 rounded bg-slate-700 px-4 py-2 text-sm font-semibold text-white
        >
          Detener
        </button>
      </div>
    </div>
  )
}
