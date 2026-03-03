import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'

export function CreatePage() {
  const navigate = useNavigate()
  const [pace, setPace] = useState('')
  const [vibe, setVibe] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const parsePace = (s: string): number | null => {
    const trimmed = s.trim()
    if (trimmed.includes(':')) {
      const [m, sec] = trimmed.split(':').map(Number)
      if (!isNaN(m) && !isNaN(sec)) return m + sec / 60
    }
    const n = parseFloat(trimmed)
    return isNaN(n) ? null : n
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const paceNum = parsePace(pace)
    if (!paceNum || paceNum <= 0) {
      setError('Enter a valid pace (e.g. 5:30 or 5.5 min/km)')
      return
    }
    if (!vibe.trim()) {
      setError('Describe your run vibe')
      return
    }
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/curation', {
        pace_min_per_km: paceNum,
        vibe_prompt: vibe.trim(),
      })
      navigate('/result', { state: { curation: data } })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Curation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto py-12 px-4">
      <Card>
        <CardHeader>
          <CardTitle>Create your run playlist</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Target pace (min/km)
              </label>
              <Input
                placeholder="e.g. 5:30 or 5.5"
                value={pace}
                onChange={(e) => setPace(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Vibe
              </label>
              <Input
                placeholder="e.g. cyberpunk city run, chill morning jog"
                value={vibe}
                onChange={(e) => setVibe(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? 'Curating...' : 'Generate playlist'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
