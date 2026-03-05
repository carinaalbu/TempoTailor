/**
 * Fetch a fresh Deezer preview URL for the given track ID.
 * Deezer preview URLs expire; this fetches a new one on demand.
 */
export async function fetchFreshPreviewUrl(deezerTrackId: number): Promise<string> {
  const API_BASE = import.meta.env.VITE_API_URL || '/api'
  const res = await fetch(`${API_BASE}/audio/preview/${deezerTrackId}`)
  if (!res.ok) {
    throw new Error('Preview not available for this track')
  }
  const data = await res.json()
  const url = data?.preview_url
  if (!url || typeof url !== 'string') {
    throw new Error('Invalid preview URL response')
  }
  return url
}
