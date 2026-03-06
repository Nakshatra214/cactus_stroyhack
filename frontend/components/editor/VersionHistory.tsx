'use client';

import { useState, useEffect } from 'react';
import { Scene } from '@/lib/store';
import { getSceneVersions, revertScene } from '@/lib/api';
import toast from 'react-hot-toast';

interface VersionHistoryProps {
    scene: Scene;
    onRevert: () => Promise<void>;
}

interface SceneVersionEntry {
    version: number;
    script: string;
    visual_prompt: string;
    image_url: string | null;
    confidence_score: number;
    created_at: string;
}

export default function VersionHistory({ scene, onRevert }: VersionHistoryProps) {
    const [versions, setVersions] = useState<SceneVersionEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [reverting, setReverting] = useState<number | null>(null);

    useEffect(() => {
        loadVersions();
    }, [scene.id]);

    async function loadVersions() {
        setLoading(true);
        try {
            const data = await getSceneVersions(scene.id);
            setVersions(data.versions);
        } catch (error) {
            console.error('Failed to load versions:', error);
        } finally {
            setLoading(false);
        }
    }

    async function handleRevert(version: number) {
        setReverting(version);
        try {
            await revertScene(scene.id, version);
            toast.success(`Reverted to v${version}`);
            await onRevert();
            await loadVersions();
        } catch (error) {
            toast.error('Failed to revert');
        } finally {
            setReverting(null);
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white flex items-center gap-2">
                    📋 Version History
                </h3>
                <span className="text-xs text-dark-300">
                    Current: v{scene.version}
                </span>
            </div>

            {/* Current Version */}
            <div className="bg-primary-600/10 border border-primary-500/30 rounded-xl p-3">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-semibold text-primary-400">
                        v{scene.version} — Current
                    </span>
                    <span className="text-[10px] text-dark-300">Active</span>
                </div>
                <p className="text-xs text-dark-100 line-clamp-2">{scene.script}</p>
            </div>

            {/* Previous Versions */}
            {loading ? (
                <div className="flex justify-center py-8">
                    <div className="w-6 h-6 border-2 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                </div>
            ) : versions.length === 0 ? (
                <div className="text-center py-8">
                    <p className="text-dark-300 text-sm">No previous versions</p>
                    <p className="text-dark-400 text-xs mt-1">Edit the scene to create version history</p>
                </div>
            ) : (
                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                    {versions.map((v) => (
                        <div
                            key={v.version}
                            className="bg-dark-700 rounded-xl p-3 group hover:bg-dark-600 transition-colors"
                        >
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs font-medium text-white">
                                    v{v.version}
                                </span>
                                <div className="flex items-center gap-2">
                                    <span className="text-[10px] text-dark-300">
                                        {Math.round(v.confidence_score * 100)}%
                                    </span>
                                    <button
                                        onClick={() => handleRevert(v.version)}
                                        disabled={reverting === v.version}
                                        className="text-[10px] bg-dark-500 hover:bg-primary-600 text-dark-200 hover:text-white px-2 py-0.5 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                                    >
                                        {reverting === v.version ? '...' : '↩ Revert'}
                                    </button>
                                </div>
                            </div>
                            <p className="text-xs text-dark-200 line-clamp-2">{v.script}</p>
                            <p className="text-[10px] text-dark-400 mt-1">{v.created_at}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
