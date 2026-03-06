'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { Scene } from '@/lib/store';

interface VideoPreviewProps {
    videoUrl: string | null;
    scene: Scene | null;
    scenes?: Scene[];
    onSceneChange?: (sceneId: number) => void;
}

export default function VideoPreview({ videoUrl, scene, scenes = [], onSceneChange }: VideoPreviewProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [videoError, setVideoError] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [slideshowIndex, setSlideshowIndex] = useState(0);
    const [slideshowProgress, setSlideshowProgress] = useState(0);
    const timerRef = useRef<NodeJS.Timeout | null>(null);
    const progressRef = useRef<NodeJS.Timeout | null>(null);

    // Reset video error when URL changes
    useEffect(() => {
        setVideoError(false);
    }, [videoUrl]);

    // Get all scenes with images for slideshow
    const slideshowScenes = scenes.length > 0 ? scenes.filter(s => s.image_url) : (scene?.image_url ? [scene] : []);
    const currentSlide = slideshowScenes[slideshowIndex] || scene;

    // Slideshow playback
    const stopSlideshow = useCallback(() => {
        if (timerRef.current) clearTimeout(timerRef.current);
        if (progressRef.current) clearInterval(progressRef.current);
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
        setIsPlaying(false);
        setSlideshowProgress(0);
    }, []);

    const playSlideshow = useCallback(() => {
        if (slideshowScenes.length === 0) return;
        setIsPlaying(true);
        setSlideshowIndex(0);
        setSlideshowProgress(0);
    }, [slideshowScenes.length]);

    // Advance slides when playing
    useEffect(() => {
        if (!isPlaying || slideshowScenes.length === 0) return;

        const currentScene = slideshowScenes[slideshowIndex];
        if (!currentScene) {
            stopSlideshow();
            return;
        }

        const duration = (currentScene.duration || 5) * 1000;

        // Notify parent of scene change
        if (onSceneChange) onSceneChange(currentScene.id);

        // Play audio for this scene
        if (audioRef.current && currentScene.audio_url) {
            audioRef.current.src = currentScene.audio_url;
            audioRef.current.play().catch(() => { });
        }

        // Progress bar
        const startTime = Date.now();
        progressRef.current = setInterval(() => {
            const elapsed = Date.now() - startTime;
            setSlideshowProgress(Math.min(100, (elapsed / duration) * 100));
        }, 50);

        // Next slide timer
        timerRef.current = setTimeout(() => {
            if (progressRef.current) clearInterval(progressRef.current);
            setSlideshowProgress(0);

            if (slideshowIndex < slideshowScenes.length - 1) {
                setSlideshowIndex(prev => prev + 1);
            } else {
                stopSlideshow();
            }
        }, duration);

        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
            if (progressRef.current) clearInterval(progressRef.current);
        };
    }, [isPlaying, slideshowIndex, slideshowScenes, onSceneChange, stopSlideshow]);

    // Determine if we should use slideshow mode
    const useSlideshowMode = videoError || !videoUrl;

    return (
        <div className="glass-card overflow-hidden">
            {/* Video / Slideshow Player */}
            <div className="aspect-video bg-dark-800 relative">
                {!useSlideshowMode ? (
                    <video
                        ref={videoRef}
                        key={videoUrl}
                        src={videoUrl}
                        controls
                        className="w-full h-full object-contain"
                        onError={() => setVideoError(true)}
                    >
                        Your browser does not support the video tag.
                    </video>
                ) : currentSlide?.image_url ? (
                    <div className="w-full h-full relative">
                        {/* Scene Image */}
                        <img
                            src={currentSlide.image_url}
                            alt={currentSlide.scene_title}
                            className="w-full h-full object-contain transition-opacity duration-500"
                        />

                        {/* Overlay with scene info */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent p-5">
                            <p className="text-white text-sm font-semibold mb-1">{currentSlide.scene_title}</p>
                            <p className="text-dark-200 text-xs line-clamp-2">{currentSlide.script}</p>
                        </div>

                        {/* Play/Pause Controls */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            {!isPlaying && (
                                <button
                                    onClick={playSlideshow}
                                    className="w-16 h-16 rounded-full bg-primary-600/80 hover:bg-primary-500 flex items-center justify-center text-white text-2xl transition-all hover:scale-110 shadow-lg shadow-primary-500/30"
                                >
                                    ▶
                                </button>
                            )}
                        </div>

                        {isPlaying && (
                            <button
                                onClick={stopSlideshow}
                                className="absolute top-3 right-3 w-8 h-8 rounded-lg bg-black/50 hover:bg-black/70 flex items-center justify-center text-white text-xs transition-all"
                            >
                                ⏸
                            </button>
                        )}

                        {/* Slide counter */}
                        {slideshowScenes.length > 1 && (
                            <div className="absolute top-3 left-3 bg-black/60 text-white text-xs px-2.5 py-1 rounded-lg">
                                {slideshowIndex + 1} / {slideshowScenes.length}
                            </div>
                        )}

                        {/* Progress bar */}
                        {isPlaying && (
                            <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/30">
                                <div
                                    className="h-full bg-gradient-to-r from-primary-500 to-accent-cyan transition-all duration-100"
                                    style={{ width: `${slideshowProgress}%` }}
                                />
                            </div>
                        )}

                        {/* Hidden audio element */}
                        <audio ref={audioRef} preload="auto" />
                    </div>
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <div className="text-center">
                            <div className="text-5xl mb-3 opacity-40">🎬</div>
                            <p className="text-dark-300 text-sm">No video preview available</p>
                            <p className="text-dark-400 text-xs mt-1">Generate visuals and build video to preview</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Scene Info Bar */}
            {currentSlide && (
                <div className="px-4 py-3 border-t border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <span className="bg-primary-600/20 text-primary-400 text-xs px-2 py-1 rounded-lg font-medium">
                            Scene {currentSlide.scene_index + 1}
                        </span>
                        <span className="text-sm text-white font-medium truncate max-w-[200px]">
                            {currentSlide.scene_title}
                        </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-dark-200">
                        <span>v{currentSlide.version}</span>
                        <span>•</span>
                        <span>{currentSlide.duration}s</span>
                        <span>•</span>
                        {useSlideshowMode && (
                            <>
                                <span className="text-accent-cyan">Slideshow</span>
                                <span>•</span>
                            </>
                        )}
                        <span className={`${currentSlide.status === 'completed' ? 'text-accent-green' :
                                currentSlide.status === 'generating' ? 'text-accent-orange animate-pulse' :
                                    'text-dark-300'
                            }`}>
                            {currentSlide.status}
                        </span>
                    </div>
                </div>
            )}

            {/* Scene Navigation Dots (slideshow mode) */}
            {useSlideshowMode && slideshowScenes.length > 1 && (
                <div className="px-4 py-2 border-t border-white/5 flex items-center justify-center gap-2">
                    {slideshowScenes.map((s, i) => (
                        <button
                            key={s.id}
                            onClick={() => {
                                setSlideshowIndex(i);
                                if (onSceneChange) onSceneChange(s.id);
                            }}
                            className={`w-2 h-2 rounded-full transition-all ${i === slideshowIndex
                                    ? 'bg-primary-500 w-4'
                                    : 'bg-dark-400 hover:bg-dark-300'
                                }`}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
