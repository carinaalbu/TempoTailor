import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { Button } from '../components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card'

interface Draft {
  id: number
  title: string
  vibe_score: number | null
  created_at: string
  updated_at: string
}

export function HistoryPage() {
  const navigate = useNavigate()
  const [drafts, setDrafts] = useState<Draft[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/drafts')
      .then(({ data }) => setDrafts(data))
      .catch(() => setDrafts([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <p className="text-gray-400">Loading drafts...</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">My runs</h1>
        <Button onClick={() => navigate('/create')}>Create new</Button>
      </div>

      {drafts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-gray-400">
            No drafts yet. Create your first run playlist.
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-4">
          {drafts.map((d) => (
            <Card
              key={d.id}
              className="cursor-pointer hover:border-gray-600 transition-colors"
              onClick={() => navigate(`/draft/${d.id}`)}
            >
              <CardHeader>
                <CardTitle>{d.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-400">
                  {d.vibe_score != null ? `Vibe: ${d.vibe_score}/100 · ` : ''}
                  {new Date(d.updated_at).toLocaleDateString()}
                </p>
              </CardContent>
            </Card>
          ))}
        </ul>
      )}
    </div>
  )
}
