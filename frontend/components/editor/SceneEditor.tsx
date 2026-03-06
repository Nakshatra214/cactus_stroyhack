'use client';

import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';

import { editScene, regenerateScene } from '@/lib/api';
import { Scene } from '@/lib/store';

interface SceneEditorProps {
    scene: Scene;
    onUpdate: () => Promise<void>;
    editSceneSocket?: (scene: Scene, instruction: string) => void;
    statusMessage?: string;
}

function toLayersText(layers: string[] | undefined): string {
    if (!layers || !layers.length) return '';
    return layers.join(', ');
}

function parseLayers(text: string): string[] {
    return text
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
}

export default function SceneEditor({ scene, onUpdate, editSceneSocket, statusMessage }: SceneEditorProps) {
    const [script, setScript] = useState(scene.script);
    const [visualPrompt, setVisualPrompt] = useState(scene.visual_prompt);
    const [visualDescription, setVisualDescription] = useState(scene.visual_description || '');
    const [cameraShot, setCameraShot] = useState(scene.camera_shot || 'medium shot');
    const [animationType, setAnimationType] = useState(scene.animation_type || 'zoom');
    const [motionDirection, setMotionDirection] = useState(scene.motion_direction || 'slow zoom in');
    const [visualLayers, setVisualLayers] = useState(toLayersText(scene.visual_layers));
    const [textOverlay, setTextOverlay] = useState(scene.text_overlay || '');
    const [transition, setTransition] = useState(scene.transition || 'fade');
    const [voiceTone, setVoiceTone] = useState(scene.voice_tone);
    const [duration, setDuration] = useState(scene.duration);
    const [title, setTitle] = useState(scene.scene_title);
    const [isSaving, setIsSaving] = useState(false);
    const [isRegenerating, setIsRegenerating] = useState(false);
    const [instruction, setInstruction] = useState('');

    useEffect(() => {
        setScript(scene.script);
        setVisualPrompt(scene.visual_prompt);
        setVisualDescription(scene.visual_description || '');
        setCameraShot(scene.camera_shot || 'medium shot');
        setAnimationType(scene.animation_type || 'zoom');
        setMotionDirection(scene.motion_direction || 'slow zoom in');
        setVisualLayers(toLayersText(scene.visual_layers));
        setTextOverlay(scene.text_overlay || '');
        setTransition(scene.transition || 'fade');
        setVoiceTone(scene.voice_tone);
        setDuration(scene.duration);
        setTitle(scene.scene_title);
        setInstruction('');
    }, [scene]);

    async function handleSave() {
        setIsSaving(true);
        try {
            await editScene(scene.id, {
                script,
                visual_prompt: visualPrompt,
                visual_description: visualDescription,
                camera_shot: cameraShot,
                animation_type: animationType,
                motion_direction: motionDirection,
                visual_layers: parseLayers(visualLayers),
                text_overlay: textOverlay,
                transition,
                voice_tone: voiceTone,
                duration,
                scene_title: title,
            });
            toast.success(`Scene updated (v${scene.version + 1})`);
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

    function handleAgenticEdit() {
        if (!instruction.trim() || !editSceneSocket) return;
        editSceneSocket(scene, instruction);
        setInstruction('');
    }

    const hasChanges =
        script !== scene.script ||
        visualPrompt !== scene.visual_prompt ||
        visualDescription !== (scene.visual_description || '') ||
        cameraShot !== (scene.camera_shot || 'medium shot') ||
        animationType !== (scene.animation_type || 'zoom') ||
        motionDirection !== (scene.motion_direction || 'slow zoom in') ||
        parseLayers(visualLayers).join('|') !== (scene.visual_layers || []).join('|') ||
        textOverlay !== (scene.text_overlay || '') ||
        transition !== (scene.transition || 'fade') ||
        voiceTone !== scene.voice_tone ||
        duration !== scene.duration ||
        title !== scene.scene_title;

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white">Scene {scene.scene_index + 1}</h3>
                {hasChanges && (
                    <span className="text-[10px] bg-accent-orange/20 text-accent-orange px-2 py-0.5 rounded-full">
                        Unsaved changes
                    </span>
                )}
            </div>

            <div className="bg-primary-900/20 border border-primary-500/30 rounded-xl p-3">
                <label className="text-xs text-primary-400 font-medium block mb-2">
                    Agentic Scene Edit
                    {statusMessage && (
                        <span className="ml-2 bg-primary-500/20 px-2 py-0.5 rounded-full text-[10px] animate-pulse">
                            {statusMessage}
                        </span>
                    )}
                </label>
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={instruction}
                        onChange={(e) => setInstruction(e.target.value)}
                        placeholder="e.g. make this scene more data-focused"
                        className="flex-1 bg-dark-800 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 transition-colors"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter') handleAgenticEdit();
                        }}
                    />
                    <button
                        onClick={handleAgenticEdit}
                        disabled={!instruction.trim() || !!statusMessage}
                        className="bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap"
                    >
                        Regenerate
                    </button>
                </div>
            </div>

            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Title</label>
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 transition-colors"
                />
            </div>

            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Narration Script</label>
                <textarea
                    value={script}
                    onChange={(e) => setScript(e.target.value)}
                    rows={3}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 resize-none transition-colors"
                />
            </div>

            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Visual Description</label>
                <textarea
                    value={visualDescription}
                    onChange={(e) => setVisualDescription(e.target.value)}
                    rows={2}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 resize-none transition-colors"
                />
            </div>

            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Visual Prompt</label>
                <textarea
                    value={visualPrompt}
                    onChange={(e) => setVisualPrompt(e.target.value)}
                    rows={2}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500 resize-none transition-colors"
                />
            </div>

            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label className="text-xs text-dark-200 font-medium block mb-1">Camera Shot</label>
                    <input
                        type="text"
                        value={cameraShot}
                        onChange={(e) => setCameraShot(e.target.value)}
                        className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                    />
                </div>
                <div>
                    <label className="text-xs text-dark-200 font-medium block mb-1">Animation Type</label>
                    <select
                        value={animationType}
                        onChange={(e) => setAnimationType(e.target.value)}
                        className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                    >
                        <option value="zoom">zoom</option>
                        <option value="pan_left">pan_left</option>
                        <option value="pan_right">pan_right</option>
                        <option value="parallax">parallax</option>
                        <option value="infographic animation">infographic animation</option>
                        <option value="diagram drawing animation">diagram drawing animation</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
                <div>
                    <label className="text-xs text-dark-200 font-medium block mb-1">Motion Direction</label>
                    <input
                        type="text"
                        value={motionDirection}
                        onChange={(e) => setMotionDirection(e.target.value)}
                        className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                    />
                </div>
                <div>
                    <label className="text-xs text-dark-200 font-medium block mb-1">Transition</label>
                    <input
                        type="text"
                        value={transition}
                        onChange={(e) => setTransition(e.target.value)}
                        className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                    />
                </div>
            </div>

            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Visual Layers (comma-separated)</label>
                <input
                    type="text"
                    value={visualLayers}
                    onChange={(e) => setVisualLayers(e.target.value)}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                />
            </div>

            <div>
                <label className="text-xs text-dark-200 font-medium block mb-1">Text Overlay</label>
                <input
                    type="text"
                    value={textOverlay}
                    onChange={(e) => setTextOverlay(e.target.value)}
                    className="w-full bg-dark-700 border border-dark-400 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
                />
            </div>

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

            <div className="flex gap-2 pt-2">
                <button
                    onClick={handleSave}
                    disabled={isSaving || !hasChanges}
                    className="flex-1 btn-primary py-2.5 text-sm flex items-center justify-center gap-2"
                >
                    {isSaving ? (
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        'Save'
                    )}
                    Changes
                </button>
                <button
                    onClick={handleRegenerate}
                    disabled={isRegenerating}
                    className="flex-1 btn-secondary py-2.5 text-sm flex items-center justify-center gap-2"
                >
                    {isRegenerating ? (
                        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                        'Rebuild'
                    )}
                    Scene
                </button>
            </div>
        </div>
    );
}
