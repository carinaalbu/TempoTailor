import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "../components/ui/card";

const SPOTIFY_GENRES = ["pop", "rock", "electronic", "hip-hop", "indie", "acoustic", "jazz", "r-n-b"];
const ENERGY_PRESETS: { label: string; value: number }[] = [
  { label: "Chill", value: 0.35 },
  { label: "Moderate", value: 0.55 },
  { label: "Energetic", value: 0.75 },
  { label: "High", value: 0.9 },
];

export function CreatePage() {
  const navigate = useNavigate();
  const [pace, setPace] = useState("");
  const [vibe, setVibe] = useState("");
  const [usePreset, setUsePreset] = useState(true);
  const [genres, setGenres] = useState<string[]>([]);
  const [energy, setEnergy] = useState(0.55);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const parsePace = (s: string): number | null => {
    const trimmed = s.trim();
    if (trimmed.includes(":")) {
      const [m, sec] = trimmed.split(":").map(Number);
      if (!isNaN(m) && !isNaN(sec)) return m + sec / 60;
    }
    const n = parseFloat(trimmed);
    return isNaN(n) ? null : n;
  };

  const toggleGenre = (g: string) => {
    setGenres((prev) =>
      prev.includes(g) ? prev.filter((x) => x !== g) : [...prev, g].slice(0, 5)
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const paceNum = parsePace(pace);
    if (!paceNum || paceNum <= 0) {
      setError("Enter a valid pace (e.g. 5:30 or 5.5 min/km)");
      return;
    }
    const useStructured = usePreset && genres.length > 0;
    if (!useStructured && !vibe.trim()) {
      setError("Pick genres + energy, or describe your vibe");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const payload = useStructured
        ? {
            pace_min_per_km: paceNum,
            vibe_prompt: "",
            target_energy: energy,
            target_valence: 0.6,
            target_danceability: 0.6,
            seed_genres: genres,
          }
        : { pace_min_per_km: paceNum, vibe_prompt: vibe.trim() };
      const { data } = await api.post("/curation", payload);
      navigate("/result", { state: { curation: data } });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err instanceof Error ? err.message : "Curation failed");
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

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
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => setUsePreset(true)}
                className={`text-sm font-medium ${usePreset ? "text-white underline" : "text-gray-500"}`}
              >
                Quick preset
              </button>
              <button
                type="button"
                onClick={() => setUsePreset(false)}
                className={`text-sm font-medium ${!usePreset ? "text-white underline" : "text-gray-500"}`}
              >
                Describe vibe
              </button>
            </div>
            {usePreset ? (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Genres (pick 1–5)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {SPOTIFY_GENRES.map((g) => (
                      <button
                        key={g}
                        type="button"
                        onClick={() => toggleGenre(g)}
                        className={`px-3 py-1 rounded-full text-sm ${
                          genres.includes(g)
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:bg-muted/80"
                        }`}
                      >
                        {g}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Energy
                  </label>
                  <div className="flex gap-2">
                    {ENERGY_PRESETS.map(({ label, value }) => (
                      <button
                        key={label}
                        type="button"
                        onClick={() => setEnergy(value)}
                        className={`px-3 py-1 rounded-full text-sm ${
                          Math.abs(energy - value) < 0.05
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted text-muted-foreground hover:bg-muted/80"
                        }`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            ) : (
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
            )}
            {error && <p className="text-sm text-red-400">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? "Curating..." : "Generate playlist"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
