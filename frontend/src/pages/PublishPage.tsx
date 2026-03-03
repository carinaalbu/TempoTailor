import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'

export function PublishPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [draft, setDraft] = useState<{ id: number; title: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!id) return
    api
      .get(`/drafts/${id}`)
      .then(({ data }) => setDraft(data))
      .catch(() => setDraft(null))
      .finally(() => setLoading(false))
  }, [id])

  const handlePublish = async () => {
    if (!draft) return
    setError('')
    setPublishing(true)
    try {
      await api.post(`/drafts/${draft.id}/publish`)
      setSuccess(true)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to publish')
    } finally {
      setPublishing(false)
    }
  }

  if (loading || !draft) {
    return (
      <div className="max-w-xl mx-auto py-12 px-4">
        <p className="text-gray-400">Loading...</p>
      </div>
    )
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
            <Button onClick={() => navigate('/history')}>Back to My runs</Button>
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
          {error && <p className="text-sm text-red-400 mb-4">{error}</p>}
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
