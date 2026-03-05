import { useRef, useState } from "react";
import { fetchFreshPreviewUrl } from "../lib/audio";

export interface PreviewPlayOptions {
  deezerTrackId?: number | null;
  previewUrl?: string | null;
}

interface PreviewPlayerProps {
  trackId: string;
  deezerTrackId?: number | null;
  previewUrl?: string | null;
  isPlaying: boolean;
  isLoading?: boolean;
  onPlay: (trackId: string, options: PreviewPlayOptions) => void;
  onPause: () => void;
}

function PlayIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden
    >
      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
    </svg>
  );
}

function LoadingSpinner() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      className="animate-spin"
      aria-hidden
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeDasharray="32"
        strokeDashoffset="12"
      />
    </svg>
  );
}

export function PreviewPlayer({
  trackId,
  deezerTrackId,
  previewUrl,
  isPlaying,
  isLoading = false,
  onPlay,
  onPause,
}: PreviewPlayerProps) {
  const canPlay = Boolean(deezerTrackId || previewUrl);

  const handleClick = () => {
    if (!canPlay) return;
    if (isPlaying) {
      onPause();
    } else {
      onPlay(trackId, { deezerTrackId, previewUrl });
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={!canPlay || isLoading}
      aria-label={
        isLoading
          ? "Loading preview"
          : isPlaying
            ? "Pause preview"
            : "Play preview"
      }
      className="flex items-center justify-center w-8 h-8 rounded-full bg-gray-700 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors"
    >
      {isLoading ? (
        <LoadingSpinner />
      ) : isPlaying ? (
        <PauseIcon />
      ) : (
        <PlayIcon />
      )}
    </button>
  );
}

export function usePreviewPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const play = async (
    trackId: string,
    options: PreviewPlayOptions
  ): Promise<void> => {
    const audio = audioRef.current;
    if (!audio) return;

    if (playingId === trackId) {
      audio.pause();
      setPlayingId(null);
      return;
    }

    setError(null);

    let url: string | null = null;

    if (options.deezerTrackId) {
      setLoadingId(trackId);
      try {
        url = await fetchFreshPreviewUrl(options.deezerTrackId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load preview");
        setLoadingId(null);
        return;
      } finally {
        setLoadingId(null);
      }
    } else if (options.previewUrl) {
      url = options.previewUrl;
    }

    if (!url) {
      setError("Preview not available");
      return;
    }

    audio.src = url;
    audio.play().catch(() => {
      setPlayingId(null);
      setError("Playback failed");
    });
    setPlayingId(trackId);
  };

  const pause = () => {
    const audio = audioRef.current;
    if (audio) audio.pause();
    setPlayingId(null);
  };

  const handleEnded = () => setPlayingId(null);

  return {
    audioRef,
    playingId,
    loadingId,
    error,
    play,
    pause,
    handleEnded,
  };
}
