import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'
import { PublishPageSkeleton } from '../components/PublishPageSkeleton'

interface PublishResponse {
  playlist_id: string
  playlist_url: string
}

export function PublishPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { reAuthorize } = useAuth()
  const [draft, setDraft] = useState<{ id: number; title: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [publishing, setPublishing] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [playlistUrl, setPlaylistUrl] = useState<string | null>(null)

  const loadDraft = useCallback(() => {
    if (!id) return
    setLoading(true)
    setFetchError(null)
    api
      .get(`/drafts/${id}`)
      .then(({ data }) => {
        setDraft(data)
        setFetchError(null)
      })
      .catch((err) => {
        setDraft(null)
        const detail = err.response?.data?.detail
        setFetchError(
          typeof detail === 'string' ? detail : 'Failed to load draft. Please try again.'
        )
      })
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    loadDraft()
  }, [loadDraft])

  const handlePublish = async () => {
    if (!draft) return
    setError('')
    setPublishing(true)
    try {
      const { data } = await api.post<PublishResponse>(`/drafts/${draft.id}/publish`)
      setPlaylistUrl(data.playlist_url || null)
      setSuccess(true)
    } catch (err: unknown) {
      const detail =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null
      setError(
        typeof detail === 'string' ? detail : err instanceof Error ? err.message : 'Failed to publish'
      )
    } finally {
      setPublishing(false)
    }
  }

  if (loading) {
    return <PublishPageSkeleton />
  }

  if (!draft && fetchError) {
    return (
      <div className="max-w-xl mx-auto py-12 px-4">
        <Card>
          <CardHeader>
            <CardTitle>Could not load draft</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-400 mb-4">{fetchError}</p>
            <Button onClick={loadDraft}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!draft) {
    return <PublishPageSkeleton />
  }

  if (success) {
    return (
      <div className="max-w-xl mx-auto py-12 px-4">
        <Card>
          <CardHeader>
            <CardTitle>Published!</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-300 mb-4">
              Your playlist &quot;{draft.title}&quot; has been created on Spotify.
            </p>
            {playlistUrl && (
              <a
                href={playlistUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block text-green-400 hover:text-green-300 underline mb-4"
              >
                Open in Spotify
              </a>
            )}
            <div className="flex gap-4 mt-4">
              <Button onClick={() => navigate('/history')}>Back to My runs</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-xl mx-auto py-12 px-4">
      <Card>
        <CardHeader>
          <CardTitle>Publish to Spotify</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-300 mb-4">
            Create a public playlist &quot;{draft.title}&quot; on your Spotify account?
          </p>
          {error && (
            <div className="mb-4">
              <p className="text-sm text-red-400">{error}</p>
              <p className="text-xs text-gray-500 mt-1">
                If it keeps failing, remove this app at{' '}
                <a
                  href="https://www.spotify.com/account/apps"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-green-400 hover:underline"
                >
                  spotify.com/account/apps
                </a>{' '}
                and log in again.
              </p>
              {(error.toLowerCase().includes('log out') ||
                error.toLowerCase().includes('log in') ||
                error.toLowerCase().includes('denied') ||
                error.toLowerCase().includes('permission') ||
                error.toLowerCase().includes('403') ||
                error.toLowerCase().includes('forbidden')) && (
                <Button
                  variant="secondary"
                  className="mt-2"
                  onClick={reAuthorize}
                >
                  Log out and re-authorize
                </Button>
              )}
            </div>
          )}
          <div className="flex gap-4">
            <Button onClick={handlePublish} disabled={publishing}>
              {publishing ? 'Publishing...' : 'Save to Spotify'}
            </Button>
            <Button variant="secondary" onClick={() => navigate(`/draft/${draft.id}`)}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
