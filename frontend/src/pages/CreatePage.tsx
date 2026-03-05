import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

const PACE_MIN = 4
const PACE_MAX = 9
const PACE_STEP = 0.5

function formatPace(n: number): string {
  const m = Math.floor(n)
  const sec = Math.round((n - m) * 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

export function CreatePage() {
  const navigate = useNavigate()
  const [pace, setPace] = useState(5.5)
  const [vibe, setVibe] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!vibe.trim()) {
      setError('Describe your vibe to generate a playlist')
      return
    }
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/curation', {
        pace_min_per_km: pace,
        vibe_prompt: vibe.trim(),
      })
      navigate('/result', { state: { curation: data } })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err instanceof Error ? err.message : 'Curation failed')
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen mesh-gradient text-white">
      <div className="max-w-xl mx-auto py-16 px-6">
        <div className="bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 p-8 md:p-10">
          <h1 className="text-2xl font-bold text-white mb-2">
            Create your run playlist
          </h1>
          <p className="text-gray-400 text-sm mb-6">
            Describe the vibe and we&apos;ll curate a playlist to match.
          </p>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="pt-8">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Target pace (min/km)
              </label>
              <div className="flex items-center gap-4 mt-6">
                <div className="pace-slider-wrapper flex-1">
                  <input
                    type="range"
                    min={PACE_MIN}
                    max={PACE_MAX}
                    step={PACE_STEP}
                    value={pace}
                    onChange={(e) => setPace(parseFloat(e.target.value))}
                    className="pace-slider w-full cursor-pointer"
                  />
                </div>
                <span className="text-white font-medium tabular-nums min-w-16">
                  {formatPace(pace)}
                </span>
              </div>
            </div>

            <div>
              <label
                htmlFor="vibe"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Vibe
              </label>
              <textarea
                id="vibe"
                placeholder="e.g. cyberpunk city run, chill morning jog, upbeat summer vibes"
                value={vibe}
                onChange={(e) => setVibe(e.target.value)}
                rows={4}
                className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-400/50 focus:border-green-400/50 resize-none"
              />
            </div>

            {error && (
              <p className="text-sm text-red-400">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-8 py-3 rounded-full font-medium text-white bg-black/80 border-2 border-green-400 shadow-[0_0_20px_rgba(74,222,128,0.3)] hover:shadow-[0_0_30px_rgba(74,222,128,0.5)] transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Curating...' : 'Generate playlist'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
