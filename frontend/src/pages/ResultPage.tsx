import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'

interface CurationTrack {
  id: string
  name: string
  artists: string[]
  preview_url: string | null
}

interface CurationState {
  track_ids: string[]
  tracks: CurationTrack[]
  vibe_score: number
  curator_note: string
  target_bpm: number
  generated_title: string
}

export function ResultPage() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const curation = state?.curation as CurationState | undefined
  const [title, setTitle] = useState(curation?.generated_title ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  if (!curation) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <p className="text-gray-400">No curation data. Start from the create page.</p>
        <Button className="mt-4" onClick={() => navigate('/create')}>
          Go back
        </Button>
      </div>
    )
  }

  const handleSave = async () => {
    setError('')
    setSaving(true)
    try {
      await api.post('/drafts', {
        title: title || curation.generated_title,
        vibe_prompt: null,
        target_bpm: curation.target_bpm,
        vibe_score: curation.vibe_score,
        curator_note: curation.curator_note,
        track_ids: curation.track_ids,
        tracks: curation.tracks.map((t) => ({
          spotify_track_id: t.id,
          name: t.name,
          artists: t.artists,
          preview_url: t.preview_url,
        })),
      })
      navigate('/history')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Your curated playlist</h1>
        <Button variant="secondary" onClick={() => navigate('/create')}>
          Back
        </Button>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Title</CardTitle>
        </CardHeader>
        <CardContent>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Playlist title"
          />
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-gray-400">
            Vibe score: {curation.vibe_score}/100 · Target BPM: {curation.target_bpm}
          </p>
          <p className="text-sm text-gray-300">{curation.curator_note}</p>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Tracks ({curation.tracks.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {curation.tracks.map((t, i) => (
              <li key={t.id} className="flex items-center gap-4">
                <span className="text-gray-500 w-6">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{t.name}</p>
                  <p className="text-sm text-gray-400 truncate">
                    {t.artists.join(', ')}
                  </p>
                </div>
                {t.preview_url && (
                  <audio controls src={t.preview_url} className="h-8 w-32" />
                )}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-400 mb-4">{error}</p>}
      <Button onClick={handleSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save as draft'}
      </Button>
    </div>
  )
}
