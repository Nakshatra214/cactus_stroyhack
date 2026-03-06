'use client';

import { useState } from 'react';
import { Scene } from '@/lib/store';
import { editScene, regenerateScene } from '@/lib/api';
import toast from 'react-hot-toast';

interface SceneEditorProps {
    scene: Scene;
    onUpdate: () => Promise<void>;
}

export default function SceneEditor({ scene, onUpdate }: SceneEditorProps) {
    const [script, setScript] = useState(scene.script);
    const [visualPrompt, setVisualPrompt] = useState(scene.visual_prompt);
    const [voiceTone, setVoiceTone] = useState(scene.voice_tone);
    const [duration, setDuration] = useState(scene.duration);
    const [title, setTitle] = useState(scene.scene_title);
    const [isSaving, setIsSaving] = useState(false);
    const [isRegenerating, setIsRegenerating] = useState(false);

    // Sync state when scene changes
    const [prevSceneId, setPrevSceneId] = useState(scene.id);
    if (scene.id !== prevSceneId) {
        setPrevSceneId(scene.id);
        setScript(scene.script);
        setVisualPrompt(scene.visual_prompt);
        setVoiceTone(scene.voice_tone);
        setDuration(scene.duration);
        setTitle(scene.scene_title);
    }

    async function handleSave() {
        setIsSaving(true);
        try {
            await editScene(scene.id, {
                script,
                visual_prompt: visualPrompt,
                voice_tone: voiceTone,
                duration,
                scene_title: title,
            });
            toast.success('Scene updated (v' + (scene.version + 1) + ')');
            await onUpdate();
        } catch (error) {
            toast.error('Failed to save scene');
        } finally {
            setIsSaving(false);
        }
    }

    async function handleRegenerate() {
        setIsRegenerating(true);
        try {
            toast.loading('Regenerating scene...', { id: 'regen' });
            await regenerateScene(scene.id);
            toast.success('Scene regenerated!', { id: 'regen' });
            await onUpdate();
        } catch (error) {
            toast.error('Failed to regenerate', { id: 'regen' });
        } finally {
            setIsRegenerating(false);
        }
    }

    const hasChanges =
        script !== scene.script ||
        visualPrompt !== scene.visual_prompt ||
        voiceTone !== scene.voice_tone ||
        duration !== scene.duration ||
        title !== scene.scene_title;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white flex items-center gap-2">
                    ✏️ Scene {scene.scene_index + 1}
                </h3>
                {hasChanges && (
                    <span className="text-[10px] bg-accent-orange/20 text-accent-orange px-2 py-0.5 rounded-full">
                        Unsaved changes
                    </span>
                )}
            </div>

            {/* Title */}
            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Title</label>
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 transition-colors"
                />
            </div>

            {/* Script / Narration */}
            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Narration Script</label>
                <textarea
                    value={script}
                    onChange={(e) => setScript(e.target.value)}
                    rows={4}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 resize-none transition-colors"
                />
            </div>

            {/* Visual Prompt */}
            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Visual Prompt</label>
                <textarea
                    value={visualPrompt}
                    onChange={(e) => setVisualPrompt(e.target.value)}
                    rows={2}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 resize-none transition-colors"
                />
            </div>

            {/* Voice & Duration Row */}
            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label className="text-xs text-dark-200 font-medium block mb-1">Voice Tone</label>
                    <select
                        value={voiceTone}
                        onChange={(e) => setVoiceTone(e.target.value)}
                        className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                    >
                        <option value="neutral">Neutral</option>
                        <option value="professional">Professional</option>
                        <option value="friendly">Friendly</option>
                        <option value="enthusiastic">Enthusiastic</option>
                        <option value="calm">Calm</option>
                    </select>
                </div>
                <div>
                    <label className="text-xs text-dark-200 font-medium block mb-1">Duration (s)</label>
                    <input
                        type="number"
                        value={duration}
                        onChange={(e) => setDuration(parseFloat(e.target.value) || 5)}
                        min={2}
                        max={60}
                        step={0.5}
                        className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                    />
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-2">
                <button
                    onClick={handleSave}
                    disabled={isSaving || !hasChanges}
                    className="flex-1 btn-primary py-2.5 text-sm flex items-center justify-center gap-2"
                >
                    {isSaving ? (
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : '💾'}
                    Save Changes
                </button>
                <button
                    onClick={handleRegenerate}
                    disabled={isRegenerating}
                    className="flex-1 btn-secondary py-2.5 text-sm flex items-center justify-center gap-2"
                >
                    {isRegenerating ? (
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : '🔄'}
                    Regenerate
                </button>
            </div>
        </div>
    );
}
