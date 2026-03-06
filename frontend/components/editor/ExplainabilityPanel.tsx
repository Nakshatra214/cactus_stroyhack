'use client';

import { Scene } from '@/lib/store';

interface ExplainabilityPanelProps {
    scene: Scene;
}

export default function ExplainabilityPanel({ scene }: ExplainabilityPanelProps) {
    const confidencePercent = Math.round(scene.confidence_score * 100);
    const confidenceLevel =
        confidencePercent >= 85 ? { label: 'High', color: 'text-accent-green', bg: 'bg-accent-green' } :
            confidencePercent >= 70 ? { label: 'Medium', color: 'text-accent-orange', bg: 'bg-accent-orange' } :
                { label: 'Low', color: 'text-red-400', bg: 'bg-red-400' };

    return (
        <div className="space-y-5">
            <h3 className="font-semibold text-white flex items-center gap-2">
                🔍 AI Explainability
            </h3>

            {/* Confidence Score */}
            <div className="bg-dark-700 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-dark-200 font-medium">Confidence Score</span>
                    <span className={`text-sm font-bold ${confidenceLevel.color}`}>
                        {confidencePercent}%
                        <span className="text-xs font-normal ml-1">({confidenceLevel.label})</span>
                    </span>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-dark-600 rounded-full h-3 overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-700 ${confidenceLevel.bg}`}
                        style={{
                            width: `${confidencePercent}%`,
                            opacity: 0.8,
                        }}
                    />
                </div>

                {/* Heatmap gradient indicator */}
                <div className="mt-2 flex items-center gap-1">
                    <div className="flex-1 h-1.5 rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 opacity-50" />
                </div>
                <div className="flex justify-between text-[10px] text-dark-300 mt-0.5">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                </div>
            </div>

            {/* Source Reference */}
            <div className="bg-dark-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm">📚</span>
                    <span className="text-xs text-dark-200 font-medium">Source Reference</span>
                </div>
                <p className="text-sm text-white leading-relaxed">
                    {scene.source_reference || 'No source reference available'}
                </p>
            </div>

            {/* AI Reasoning */}
            <div className="bg-dark-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm">🧠</span>
                    <span className="text-xs text-dark-200 font-medium">AI Reasoning</span>
                </div>
                <div className="space-y-2 text-sm text-dark-100">
                    <div className="flex items-start gap-2">
                        <span className="text-accent-cyan mt-0.5">•</span>
                        <span>Content was extracted and analyzed by the Script Agent</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <span className="text-accent-cyan mt-0.5">•</span>
                        <span>Visual prompt generated to match narration context</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <span className="text-accent-cyan mt-0.5">•</span>
                        <span>Fact-checked against source material ({confidencePercent}% match)</span>
                    </div>
                </div>
            </div>

            {/* Scene Metadata */}
            <div className="bg-dark-700 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                    <span className="text-sm">📊</span>
                    <span className="text-xs text-dark-200 font-medium">Scene Metadata</span>
                </div>
                <div className="grid grid-cols-2 gap-y-2 text-xs">
                    <span className="text-dark-300">Version</span>
                    <span className="text-white text-right">v{scene.version}</span>
                    <span className="text-dark-300">Duration</span>
                    <span className="text-white text-right">{scene.duration}s</span>
                    <span className="text-dark-300">Voice Tone</span>
                    <span className="text-white text-right capitalize">{scene.voice_tone}</span>
                    <span className="text-dark-300">Status</span>
                    <span className={`text-right ${scene.status === 'completed' ? 'text-accent-green' : 'text-accent-orange'
                        }`}>{scene.status}</span>
                </div>
            </div>
        </div>
    );
}
