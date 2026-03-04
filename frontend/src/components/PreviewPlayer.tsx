import { useRef, useState } from 'react'

interface PreviewPlayerProps {
  trackId: string
  previewUrl: string
  isPlaying: boolean
  onPlay: (trackId: string, previewUrl: string) => void
  onPause: () => void
}

function PlayIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M8 5v14l11-7z" />
    </svg>
  )
}

function PauseIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
    </svg>
  )
}

export function PreviewPlayer({ trackId, previewUrl, isPlaying, onPlay, onPause }: PreviewPlayerProps) {
  const handleClick = () => {
    if (isPlaying) {
      onPause()
    } else {
      onPlay(trackId, previewUrl)
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      aria-label={isPlaying ? 'Pause preview' : 'Play preview'}
      className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 hover:bg-gray-600 text-white transition-colors"
    >
      {isPlaying ? <PauseIcon /> : <PlayIcon />}
    </button>
  )
}

export function usePreviewPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [playingId, setPlayingId] = useState<string | null>(null)

  const play = (trackId: string, previewUrl: string) => {
    const audio = audioRef.current
    if (!audio) return
    if (playingId === trackId) {
      audio.pause()
      setPlayingId(null)
      return
    }
    audio.src = previewUrl
    audio.play()
    setPlayingId(trackId)
  }

  const pause = () => {
    const audio = audioRef.current
    if (audio) audio.pause()
    setPlayingId(null)
  }

  const handleEnded = () => setPlayingId(null)

  return { audioRef, playingId, play, pause, handleEnded }
}
