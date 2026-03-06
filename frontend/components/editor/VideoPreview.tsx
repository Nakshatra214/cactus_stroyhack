'use client';

import { useState, useRef, useEffect } from 'react';
import { Scene } from '@/lib/store';

interface VideoPreviewProps {
    videoUrl: string | null;
    scene: Scene | null;
    scenes?: Scene[];
}

export default function VideoPreview({ videoUrl, scene, scenes }: VideoPreviewProps) {
    const [videoError, setVideoError] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const audioRef = useRef<HTMLAudioElement>(null);

    // Reset error state when video URL changes
    useEffect(() => {
        setVideoError(false);
        setIsPlaying(false);
        setCurrentTime(0);
    }, [videoUrl, scene?.id]);

    const hasValidVideo = videoUrl && videoUrl.trim() !== '' && !videoError;
    const hasImagePreview = scene?.image_url && scene.image_url.trim() !== '';
    const hasAudio = scene?.audio_url && scene.audio_url.trim() !== '';

    function togglePlayback() {
        if (!audioRef.current) return;
        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
        } else {
            audioRef.current.play().catch(() => { });
            setIsPlaying(true);
        }
    }

    function handleAudioTimeUpdate() {
        if (audioRef.current) {
            setCurrentTime(audioRef.current.currentTime);
        }
    }

    function handleAudioEnded() {
        setIsPlaying(false);
        setCurrentTime(0);
    }

    return (
        <div className="glass-card overflow-hidden">
            {/* Video / Image Preview */}
            <div className="aspect-video bg-dark-800 relative">
                {hasValidVideo ? (
                    /* Real video playback */
                    <video
                        key={videoUrl}
                        src={videoUrl}
                        controls
                        className="w-full h-full object-contain"
                        onError={() => setVideoError(true)}
                    >
                        Your browser does not support the video tag.
                    </video>
                ) : hasImagePreview ? (
                    /* Image + Audio preview fallback */
                    <div className="w-full h-full relative group">
                        <img
                            src={scene.image_url!}
                            alt={scene.scene_title}
                            className="w-full h-full object-contain"
                        />

                        {/* Play/Pause overlay */}
                        <button
                            onClick={togglePlayback}
                            className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                        >
                            <div className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${isPlaying
                                    ? 'bg-white/20 backdrop-blur-sm'
                                    : 'bg-primary-600/80 hover:bg-primary-500/90 shadow-lg shadow-primary-500/30'
                                }`}>
                                {isPlaying ? (
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="white">
                                        <rect x="6" y="4" width="4" height="16" rx="1" />
                                        <rect x="14" y="4" width="4" height="16" rx="1" />
                                    </svg>
                                ) : (
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="white">
                                        <polygon points="8,4 20,12 8,20" />
                                    </svg>
                                )}
                            </div>
                        </button>

                        {/* Audio element */}
                        {hasAudio && (
                            <audio
                                ref={audioRef}
                                src={scene.audio_url!}
                                onTimeUpdate={handleAudioTimeUpdate}
                                onEnded={handleAudioEnded}
                                preload="auto"
                            />
                        )}

                        {/* Bottom info overlay */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                            <p className="text-white text-sm font-medium">{scene.scene_title}</p>
                            <p className="text-dark-200 text-xs mt-1 line-clamp-2">{scene.script}</p>

                            {/* Audio progress bar */}
                            {hasAudio && (
                                <div className="mt-2 flex items-center gap-2">
                                    <button
                                        onClick={togglePlayback}
                                        className="text-white hover:text-primary-400 transition-colors"
                                    >
                                        {isPlaying ? '⏸' : '▶'}
                                    </button>
                                    <div className="flex-1 bg-white/20 rounded-full h-1.5 overflow-hidden">
                                        <div
                                            className="h-full bg-primary-400 rounded-full transition-all duration-200"
                                            style={{
                                                width: audioRef.current?.duration
                                                    ? `${(currentTime / audioRef.current.duration) * 100}%`
                                                    : '0%'
                                            }}
                                        />
                                    </div>
                                    <span className="text-[10px] text-dark-200 min-w-[40px] text-right">
                                        {Math.floor(currentTime)}s / {scene.duration}s
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* FFmpeg notice badge */}
                        {videoError && (
                            <div className="absolute top-3 left-3 bg-dark-800/80 backdrop-blur-sm text-xs text-dark-200 px-3 py-1.5 rounded-lg border border-dark-400">
                                🎞️ Showing image + audio preview (install FFmpeg for full video)
                            </div>
                        )}
                        {!videoUrl && (
                            <div className="absolute top-3 left-3 bg-dark-800/80 backdrop-blur-sm text-xs text-dark-200 px-3 py-1.5 rounded-lg border border-dark-400">
                                🎨 Image + Audio Preview
                            </div>
                        )}
                    </div>
                ) : (
                    /* No preview at all */
                    <div className="w-full h-full flex items-center justify-center">
                        <div className="text-center">
                            <div className="text-5xl mb-3 opacity-40">🎬</div>
                            <p className="text-dark-300 text-sm">No preview available</p>
                            <p className="text-dark-400 text-xs mt-1">Generate visuals and build video to preview</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Scene Info Bar */}
            {scene && (
                <div className="px-4 py-3 border-t border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="bg-primary-600/20 text-primary-400 text-xs px-2 py-1 rounded-lg font-medium">
                            Scene {scene.scene_index + 1}
                        </span>
                        <span className="text-sm text-white font-medium truncate max-w-[200px]">
                            {scene.scene_title}
                        </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-dark-200">
                        <span>v{scene.version}</span>
                        <span>•</span>
                        <span>{scene.duration}s</span>
                        <span>•</span>
                        <span className={`${scene.status === 'completed' ? 'text-accent-green' :
                                scene.status === 'generating' ? 'text-accent-orange animate-pulse' :
                                    'text-dark-300'
                            }`}>
                            {scene.status}
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
