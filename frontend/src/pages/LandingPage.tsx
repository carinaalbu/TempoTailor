import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

export function LandingPage() {
  const navigate = useNavigate();
  const { user, login, logout, authError, clearAuthError } = useAuth();

  return (
    <div className="min-h-screen mesh-gradient text-white overflow-hidden">
      {/* Navigation Bar */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 md:px-10 lg:px-16">
        <Link
          to="/"
          className="text-xl md:text-2xl font-bold text-white tracking-tight"
        >
          TempoTailor
        </Link>
        <div className="flex items-center gap-4 md:gap-6">
          {user ? (
            <>
              <Link
                to="/create"
                className="text-white text-sm font-medium hover:text-green-400 transition-colors"
              >
                Create
              </Link>
              <Link
                to="/history"
                className="text-white text-sm font-medium hover:text-green-400 transition-colors"
              >
                My runs
              </Link>
              <div className="flex items-center gap-2">
                <div
                  className="h-9 w-9 rounded-full overflow-hidden border border-white/20 flex-shrink-0 bg-violet-900/60"
                  aria-hidden
                >
                  {user.image_url ? (
                    <img
                      src={user.image_url}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="h-full w-full flex items-center justify-center">
                      <svg
                        className="w-5 h-5 text-violet-300"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                      </svg>
                    </div>
                  )}
                </div>
                <span className="text-sm text-gray-300 max-w-[120px] truncate hidden sm:inline">
                  {user.display_name || user.email || "Profile"}
                </span>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium rounded-full border border-white/20 hover:bg-white/5 transition-colors text-white"
              >
                Log out
              </button>
            </>
          ) : (
            <button
              onClick={login}
              className="px-4 py-2 text-sm font-medium rounded-full border border-white/20 hover:bg-white/5 transition-colors text-white"
            >
              Log in with Spotify
            </button>
          )}
        </div>
      </nav>

      <main className="relative">
        {/* Hero Section */}
        <section className="relative flex flex-col items-center justify-center px-6 pt-12 pb-20 md:pt-20 md:pb-28 lg:pt-24 lg:pb-32">
          {/* Orbit swoosh behind content - Gemini SVG, positioned so "your pace" sits in upper gap */}
          <div
            className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-visible"
            aria-hidden
          >
            <img
              src="/assets/Gemini_Generated_Image_atee5katee5katee.svg"
              alt=""
              className="w-full min-w-[1400px] max-w-[105rem] h-auto opacity-50 object-contain translate-y-32 -translate-x-[24px]"
            />
          </div>

          <div className="relative z-10 text-center max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-white mb-6">
              Playlists that match <br />
              <span className="text-green-400 drop-shadow-[0_0_15px_rgba(74,222,128,0.8)]">
                your pace
              </span>
            </h1>
            <p className="text-base md:text-lg text-gray-300 max-w-2xl mx-auto mb-10">
              Enter your target pace and describe the vibe. TempoTailor uses AI
              to curate a Spotify playlist tuned to your cadence&mdash;no more
              skipping mid-run.
            </p>

            {authError && (
              <div
                className="mb-6 px-4 py-3 rounded-lg bg-red-500/20 text-red-400 text-sm flex items-center justify-between max-w-md mx-auto"
                role="alert"
              >
                <span>{authError}</span>
                <button
                  onClick={clearAuthError}
                  className="text-red-300 hover:text-red-200 ml-2"
                  aria-label="Dismiss"
                >
                  &times;
                </button>
              </div>
            )}

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={user ? () => navigate("/create") : login}
                className="px-8 py-3 rounded-full font-medium text-white bg-green-400/80 border-2 border-green-400 shadow-[0_0_20px_rgba(74,222,128,0.3)] hover:shadow-[0_0_30px_rgba(74,222,128,0.5)] transition-shadow"
              >
                {user ? "Go to Create" : "Log in with Spotify"}
              </button>
              <button
                onClick={() =>
                  document
                    .getElementById("how-it-works")
                    ?.scrollIntoView({ behavior: "smooth" })
                }
                className="px-8 py-3 rounded-full font-medium text-white bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
              >
                See how it works
              </button>
            </div>
          </div>
        </section>

        {/* How TempoTailor works - Horizontal Timeline */}
        <section
          id="how-it-works"
          className="relative px-6 py-16 md:py-24 lg:py-32"
        >
          <h2 className="text-2xl font-bold text-white mb-16 md:mb-20 pl-4 md:pl-8 lg:pl-16">
            How TempoTailor works
          </h2>

          <div className="relative max-w-6xl mx-auto">
            {/* Connecting timeline with gradient glow */}
            <div className="absolute left-[8%] right-[8%] top-[56px] hidden lg:block z-0">
              <div
                className="h-[2px] w-full rounded-full"
                style={{
                  background:
                    "linear-gradient(90deg, rgba(245,158,11,0.5) 0%, rgba(168,85,247,0.6) 50%, rgba(20,184,166,0.5) 100%)",
                  boxShadow:
                    "0 0 12px rgba(245,158,11,0.3), 0 0 24px rgba(168,85,247,0.2), 0 0 12px rgba(20,184,166,0.3)",
                }}
              />
            </div>

            <div className="grid md:grid-cols-3 gap-8 lg:gap-10 relative">
              {/* Step 1 */}
              <div className="flex flex-col items-center">
                <div
                  className="w-11 h-11 rounded-full flex items-center justify-center font-bold text-sm z-10 shrink-0"
                  style={{
                    background: "rgba(245, 158, 11, 0.25)",
                    boxShadow: "0 0 20px rgba(245, 158, 11, 0.5)",
                    border: "2px solid rgba(245, 158, 11, 0.4)",
                  }}
                >
                  1
                </div>
                <div className="w-full mt-8 bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 overflow-hidden">
                  <div className="h-40 w-full bg-black/30 flex items-center justify-center overflow-hidden">
                    <img
                      src="/assets/step1-pace-bpm.png"
                      alt="Runner connected to BPM gauge"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Pace to BPM
                    </h3>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      We analyze your target pace to calculate the ideal BPM for
                      your run.
                    </p>
                  </div>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex flex-col items-center">
                <div
                  className="w-11 h-11 rounded-full flex items-center justify-center font-bold text-sm z-10 shrink-0"
                  style={{
                    background: "rgba(168, 85, 247, 0.25)",
                    boxShadow: "0 0 20px rgba(168, 85, 247, 0.5)",
                    border: "2px solid rgba(168, 85, 247, 0.4)",
                  }}
                >
                  2
                </div>
                <div className="w-full mt-8 bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 overflow-hidden">
                  <div className="h-40 w-full bg-black/30 flex items-center justify-center overflow-hidden">
                    <img
                      src="/assets/step2-vibe-translation.png"
                      alt="Paintbrushes with colorful smoke and Spotify logo"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Vibe translation
                    </h3>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      AI translates your description into mood, energy, and
                      genre parameters.
                    </p>
                  </div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex flex-col items-center">
                <div
                  className="w-11 h-11 rounded-full flex items-center justify-center font-bold text-sm z-10 shrink-0"
                  style={{
                    background: "rgba(20, 184, 166, 0.25)",
                    boxShadow: "0 0 20px rgba(20, 184, 166, 0.5)",
                    border: "2px solid rgba(20, 184, 166, 0.4)",
                  }}
                >
                  3
                </div>
                <div className="w-full mt-8 bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 overflow-hidden">
                  <div className="h-40 w-full bg-black/30 flex items-center justify-center overflow-hidden">
                    <img
                      src="/assets/step3-curated-quality.png"
                      alt="AI robot reviewing playlist on phone"
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="p-6">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Curated quality
                    </h3>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      A fine-tuned AI reviews every track, ensuring only the
                      highest quality fits the playlist.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="px-6 py-16 md:py-24">
          <div className="max-w-2xl mx-auto text-center">
            <div className="bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 p-8 md:p-10">
              <h3 className="text-xl font-semibold text-white mb-3">
                Ready to run with the right beats?
              </h3>
              <p className="text-gray-400 mb-6">
                {user
                  ? "Create playlists tailored to your runs in seconds."
                  : "Connect your Spotify account to create playlists tailored to your runs."}
              </p>
              <button
                onClick={user ? () => navigate("/create") : login}
                className="px-8 py-3 rounded-full font-medium text-white bg-black/80 border-2 border-green-400 shadow-[0_0_20px_rgba(74,222,128,0.3)] hover:shadow-[0_0_30px_rgba(74,222,128,0.5)] transition-shadow"
              >
                {user ? "Go to Create" : "Log in with Spotify"}
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
