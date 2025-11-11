import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import './AudioVisualizer.css'

interface AudioVisualizerProps {
  isActive: boolean
  isListening: boolean
}

const AudioVisualizer = ({ isActive, isListening }: AudioVisualizerProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    if (!isActive || !canvasRef.current) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      return
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const width = canvas.width
    const height = canvas.height
    const centerY = height / 2
    const barCount = 50
    const barWidth = width / barCount

    let phase = 0

    const draw = () => {
      ctx.clearRect(0, 0, width, height)
      
      ctx.fillStyle = 'rgba(232, 213, 196, 0.8)'
      
      for (let i = 0; i < barCount; i++) {
        const x = i * barWidth
        const amplitude = isListening ? 40 : 30
        const frequency = isListening ? 0.1 : 0.05
        const barHeight = Math.sin(i * frequency + phase) * amplitude + amplitude
        
        const y = centerY - barHeight / 2
        
        ctx.fillRect(x, y, barWidth - 2, barHeight)
      }
      
      phase += isListening ? 0.15 : 0.08
      animationRef.current = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isActive, isListening])

  if (!isActive) {
    return null
  }

  return (
    <motion.div
      className="audio-visualizer"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.3 }}
    >
      <canvas
        ref={canvasRef}
        width={400}
        height={100}
        className="visualizer-canvas"
      />
    </motion.div>
  )
}

export default AudioVisualizer
