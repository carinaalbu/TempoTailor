import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { PreviewPlayer, usePreviewPlayer } from '../components/PreviewPlayer'

interface DraftTrack {
  id: number
  spotify_track_id: string
  track_order: number
  name: string | null
  artists: string | null
  preview_url: string | null
  deezer_track_id?: number | null
}

interface Draft {
  id: number
  title: string
  vibe_score: number | null
  curator_note: string | null
  tracks: DraftTrack[]
}

export function DraftDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [draft, setDraft] = useState<Draft | null>(null)
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const { audioRef, playingId, loadingId, play, pause, handleEnded } = usePreviewPlayer()

  useEffect(() => {
    if (!id) return
    api
      .get(`/drafts/${id}`)
      .then(({ data }) => {
        setDraft(data)
        setTitle(data.title)
      })
      .catch(() => setDraft(null))
      .finally(() => setLoading(false))
  }, [id])

  const removeTrack = (trackId: string) => {
    if (!draft) return
    const kept = draft.tracks.filter((t) => t.spotify_track_id !== trackId)
    setDraft({
      ...draft,
      tracks: kept.map((t, i) => ({ ...t, id: i, track_order: i })),
    })
  }

    const handleSave = async () => {
    if (!draft) return
    setError('')
    setSaving(true)
    try {
      await api.patch(`/drafts/${draft.id}`, {
        title,
        track_ids: draft.tracks.map((t) => t.spotify_track_id),
        tracks: draft.tracks.map((t) => ({
          spotify_track_id: t.spotify_track_id,
          name: t.name,
          artists: t.artists ? t.artists.split(', ') : [],
          preview_url: t.preview_url,
          deezer_track_id: t.deezer_track_id ?? null,
        })),
      })
      setDraft({ ...draft, title })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!draft || !confirm('Delete this draft?')) return
    try {
      await api.delete(`/drafts/${draft.id}`)
      navigate('/history')
    } catch {
      setError('Failed to delete')
    }
  }

  if (loading || !draft) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Edit draft</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate('/history')}>
            Back
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            Delete
          </Button>
        </div>
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

      {draft.curator_note && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <p className="text-sm text-gray-300">{draft.curator_note}</p>
          </CardContent>
        </Card>
      )}

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Tracks ({draft.tracks.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <audio ref={audioRef} onEnded={handleEnded} className="hidden" />
          <ul className="space-y-3">
            {draft.tracks.map((t, i) => (
              <li
                key={t.spotify_track_id}
                className="flex items-center gap-4 group"
              >
                <span className="text-gray-500 w-6">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{t.name || `Track ${t.spotify_track_id}`}</p>
                  {t.artists && (
                    <p className="text-sm text-gray-400 truncate">{t.artists}</p>
                  )}
                </div>
                {(t.deezer_track_id || t.preview_url) && (
                  <PreviewPlayer
                    trackId={t.spotify_track_id}
                    deezerTrackId={t.deezer_track_id ?? null}
                    previewUrl={t.preview_url}
                    isPlaying={playingId === t.spotify_track_id}
                    isLoading={loadingId === t.spotify_track_id}
                    onPlay={play}
                    onPause={pause}
                  />
                )}
                <Button
                  variant="ghost"
                  className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300"
                  onClick={() => removeTrack(t.spotify_track_id)}
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-400 mb-4">{error}</p>}
      <div className="flex gap-4">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save changes'}
        </Button>
        <Button variant="secondary" onClick={() => navigate(`/publish/${draft.id}`)}>
          Publish to Spotify
        </Button>
      </div>
    </div>
  )
}
