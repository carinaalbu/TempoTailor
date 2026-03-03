import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

export function LandingPage() {
  const navigate = useNavigate()
  const { user, login } = useAuth()

  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-hidden">
      {/* Gradient background accents */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-green-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl" />
      </div>

      <main className="relative max-w-6xl mx-auto px-6 py-16 md:py-24">
        {/* Hero */}
        <section className="text-center mb-20 md:mb-28">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            Playlists that match
            <br />
            <span className="text-green-400">your pace</span>
          </h1>
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            Enter your target pace and describe the vibe. TempoTailor uses AI to curate
            a Spotify playlist tuned to your cadence—no more skipping mid-run.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={user ? () => navigate('/create') : login}
              className="text-base px-8 py-3 bg-green-600 hover:bg-green-500"
            >
              {user ? 'Go to Create' : 'Log in with Spotify'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
              className="text-base px-8 py-3"
            >
              See how it works
            </Button>
          </div>
        </section>

        {/* Feature highlights */}
        <section id="how-it-works" className="mb-20 md:mb-28">
          <h2 className="text-2xl md:text-3xl font-semibold text-center mb-12">
            How TempoTailor works
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="border-gray-800 bg-gray-900/60 backdrop-blur">
              <CardContent className="pt-6">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center mb-4 text-green-400 font-bold">
                  1
                </div>
                <h3 className="text-lg font-semibold mb-2">Pace to BPM</h3>
                <p className="text-gray-400 text-sm">
                  Your target pace (e.g. 5:30 min/km) is converted into an ideal cadence
                  range so the music keeps you in rhythm.
                </p>
              </CardContent>
            </Card>
            <Card className="border-gray-800 bg-gray-900/60 backdrop-blur">
              <CardContent className="pt-6">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center mb-4 text-green-400 font-bold">
                  2
                </div>
                <h3 className="text-lg font-semibold mb-2">Vibe translation</h3>
                <p className="text-gray-400 text-sm">
                  AI turns your description—like &quot;cyberpunk city run&quot;—into
                  Spotify parameters: energy, genres, and mood.
                </p>
              </CardContent>
            </Card>
            <Card className="border-gray-800 bg-gray-900/60 backdrop-blur">
              <CardContent className="pt-6">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center mb-4 text-green-400 font-bold">
                  3
                </div>
                <h3 className="text-lg font-semibold mb-2">Curated quality</h3>
                <p className="text-gray-400 text-sm">
                  An AI judge filters tracks to keep only the best fits. Preview, edit,
                  and save to your Spotify account.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* CTA */}
        <section className="text-center">
          <Card className="border-green-500/30 bg-gray-900/80 max-w-2xl mx-auto">
            <CardContent className="py-10 px-8">
              <h3 className="text-xl font-semibold mb-3">
                Ready to run with the right beats?
              </h3>
              <p className="text-gray-400 mb-6">
                Connect your Spotify account to create playlists tailored to your runs.
              </p>
              <Button onClick={login} className="text-base px-8 py-3 bg-green-600 hover:bg-green-500">
                Log in with Spotify
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  )
}
