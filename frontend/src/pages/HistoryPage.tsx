import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { PreviewPlayer, usePreviewPlayer } from '../components/PreviewPlayer'

interface DraftTrack {
  id: number
  spotify_track_id: string
  track_order: number
  name: string | null
  artists: string | null
  preview_url: string | null
}

interface Draft {
  id: number
  title: string
  vibe_prompt: string | null
  target_pace_min_per_km: number | null
  vibe_score: number | null
  curator_note: string | null
  created_at: string
  updated_at: string
  tracks: DraftTrack[]
}

const ACCENT_COLORS = [
  'bg-amber-500/20 border-amber-500/40 text-amber-200',
  'bg-sky-500/20 border-sky-500/40 text-sky-200',
  'bg-violet-500/20 border-violet-500/40 text-violet-200',
  'bg-emerald-500/20 border-emerald-500/40 text-emerald-200',
]

function formatPace(n: number | null): string {
  if (n == null) return '—'
  const m = Math.floor(n)
  const sec = Math.round((n - m) * 60)
  return `${m}:${sec.toString().padStart(2, '0')} min/km`
}

function formatDate(s: string): string {
  return new Date(s).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).toUpperCase()
}

function estimateDuration(trackCount: number): string {
  const mins = Math.round(trackCount * 3.5)
  return `${Math.floor(mins / 60)}:${(mins % 60).toString().padStart(2, '0')}`
}

export function HistoryPage() {
  const navigate = useNavigate()
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [loading, setLoading] = useState(true)
  const { audioRef, playingId, play, pause, handleEnded } = usePreviewPlayer()

  useEffect(() => {
    api
      .get<Draft[]>('/drafts')
      .then(({ data }) => setDrafts(data))
      .catch(() => setDrafts([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen mesh-gradient text-white flex items-center justify-center">
        <p className="text-gray-400">Loading runs...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen mesh-gradient text-white">
      <div className="max-w-6xl mx-auto py-10 px-6 md:px-10">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-10">
          <h1 className="text-3xl md:text-4xl font-bold text-white">My runs</h1>
          <button
            onClick={() => navigate('/create')}
            className="px-6 py-3 rounded-full font-medium text-white bg-green-400/80 border-2 border-green-400 shadow-[0_0_20px_rgba(74,222,128,0.3)] hover:shadow-[0_0_30px_rgba(74,222,128,0.5)] transition-shadow"
          >
            Create new
          </button>
        </div>

        {drafts.length === 0 ? (
          <div className="bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 p-12 text-center">
            <p className="text-gray-400">No runs yet. Create your first run playlist.</p>
          </div>
        ) : (
          <>
            <audio ref={audioRef} onEnded={handleEnded} className="hidden" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {drafts.map((d, i) => {
                const firstTrack = d.tracks?.[0]
                const accentClass = ACCENT_COLORS[i % ACCENT_COLORS.length]
                return (
                  <button
                    key={d.id}
                    type="button"
                    onClick={() => navigate(`/draft/${d.id}`)}
                    className="text-left w-full h-full group"
                  >
                    <div className="h-full bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 p-5 hover:bg-white/[0.06] hover:border-white/20 transition-all duration-200">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${accentClass} mb-3`}
                      >
                        {formatDate(d.created_at)}
                      </span>
                      <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
                        <span className="w-4 h-4 rounded-full bg-gray-500/50 flex items-center justify-center">
                          <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M13.5 5.5c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zM9.8 8.9L7 23h2.1l1.8-8 2.1 2v6h2v-7.5l-2.1-2 .6-3C14.8 12 16.8 13 19 13v-2c-1.9 0-3.5-1-4.3-2.4l-1-1.6c-.4-.6-1-1-1.7-1-.3 0-.5.1-.8.1L6 8.3V13h2V9.6l1.8-.7" />
                          </svg>
                        </span>
                        {formatPace(d.target_pace_min_per_km)}
                      </div>
                      <h2 className="text-lg font-bold text-white mb-1 group-hover:text-green-400 transition-colors">
                        {d.title}
                      </h2>
                      <p className="text-sm text-gray-400 line-clamp-2 mb-3">
                        {d.vibe_prompt || d.curator_note || 'No description'}
                      </p>
                      {d.vibe_score != null && (
                        <p className="text-xs text-gray-500 mb-4">
                          AI Vibe Score: {d.vibe_score}/100
                        </p>
                      )}
                      <div className="flex items-center gap-3 pt-3 border-t border-white/5">
                        {firstTrack?.preview_url ? (
                          <div onClick={(e) => e.stopPropagation()}>
                            <PreviewPlayer
                              trackId={firstTrack.spotify_track_id}
                              previewUrl={firstTrack.preview_url}
                              isPlaying={playingId === firstTrack.spotify_track_id}
                              onPlay={play}
                              onPause={pause}
                            />
                          </div>
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-gray-700/50 flex items-center justify-center">
                            <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M8 5v14l11-7z" />
                            </svg>
                          </div>
                        )}
                        <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
                          <div className="h-full w-0 bg-green-400/50 rounded-full" />
                        </div>
                        <span className="text-xs text-gray-500 tabular-nums">
                          0:00 / {estimateDuration(d.tracks?.length ?? 0)}
                        </span>
                        <svg className="w-5 h-5 text-green-400" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.398.082-.796-.163-.878-.561-.082-.398.163-.796.561-.878 4.52-1.041 8.52-.6 11.64 1.34.36.18.48.66.24 1.021zm1.44-3.3c-.301.42-.847.56-1.275.24-3.239-1.98-8.159-2.58-11.939-1.38-.479.14-.994-.07-1.134-.549-.14-.479.07-.994.549-1.134 4.239-1.29 9.693-.64 13.314 1.63.441.27.578.847.24 1.275zm.12-3.36C15.239 8.16 8.231 7.86 5.091 9.08c-.581.18-1.24-.12-1.44-.701-.18-.581.12-1.24.701-1.44 3.631-1.14 11.211-.82 15.671 1.56.701.39.921 1.24.531 1.921z" />
                        </svg>
                      </div>
                    </div>
                  </button>
                )
              })}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
