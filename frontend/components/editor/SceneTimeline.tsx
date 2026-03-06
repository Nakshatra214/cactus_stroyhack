'use client';

import { Scene } from '@/lib/store';

interface SceneTimelineProps {
    scenes: Scene[];
    selectedSceneId: number | null;
    onSelectScene: (id: number) => void;
}

export default function SceneTimeline({ scenes, selectedSceneId, onSelectScene }: SceneTimelineProps) {
    return (
        <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    🎞️ Scene Timeline
                </h3>
                <span className="text-xs text-dark-300">{scenes.length} scenes</span>
            </div>

            <div className="timeline-track p-2">
                <div className="flex gap-2 overflow-x-auto pb-2">
                    {scenes.map((scene) => {
                        const isSelected = scene.id === selectedSceneId;
                        const confidenceColor =
                            scene.confidence_score >= 0.85 ? 'bg-accent-green' :
                                scene.confidence_score >= 0.7 ? 'bg-accent-orange' :
                                    'bg-red-500';

                        return (
                            <button
                                key={scene.id}
                                id={`scene-${scene.id}`}
                                onClick={() => onSelectScene(scene.id)}
                                className={`flex-shrink-0 w-40 rounded-xl p-3 text-left transition-all duration-200 group ${isSelected
                                        ? 'bg-primary-600/30 border border-primary-500/50 shadow-lg shadow-primary-500/10'
                                        : 'bg-dark-600/60 border border-transparent hover:bg-dark-500/60 hover:border-dark-400'
                                    }`}
                            >
                                {/* Thumbnail */}
                                <div className="aspect-video rounded-lg bg-dark-700 mb-2 overflow-hidden relative">
                                    {scene.image_url ? (
                                        <img
                                            src={scene.image_url}
                                            alt={scene.scene_title}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-2xl opacity-30">
                                            🎨
                                        </div>
                                    )}
                                    {/* Duration badge */}
                                    <span className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded">
                                        {scene.duration}s
                                    </span>
                                </div>

                                {/* Title */}
                                <p className="text-xs font-medium text-white truncate">{scene.scene_title}</p>

                                {/* Bottom info */}
                                <div className="flex items-center justify-between mt-1.5">
                                    <span className="text-[10px] text-dark-300">v{scene.version}</span>
                                    <div className="flex items-center gap-1">
                                        <span className={`w-1.5 h-1.5 rounded-full ${confidenceColor}`} />
                                        <span className="text-[10px] text-dark-300">
                                            {Math.round(scene.confidence_score * 100)}%
                                        </span>
                                    </div>
                                </div>
                            </button>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
