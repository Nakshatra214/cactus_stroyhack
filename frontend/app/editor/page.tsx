'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { useStore } from '@/lib/store';
import { getScenes, getProject, buildVideo, getExportUrl } from '@/lib/api';
import VideoPreview from '@/components/editor/VideoPreview';
import SceneTimeline from '@/components/editor/SceneTimeline';
import SceneEditor from '@/components/editor/SceneEditor';
import ExplainabilityPanel from '@/components/editor/ExplainabilityPanel';
import VersionHistory from '@/components/editor/VersionHistory';
import toast from 'react-hot-toast';

export default function EditorPage() {
    const searchParams = useSearchParams();
    const projectId = searchParams.get('project');
    const { project, setProject, scenes, setScenes, selectedSceneId, setSelectedSceneId, isLoading, setLoading } = useStore();
    const [activePanel, setActivePanel] = useState<'editor' | 'explain' | 'versions'>('editor');
    const [isRebuilding, setIsRebuilding] = useState(false);

    // Load project data
    useEffect(() => {
        if (projectId) {
            loadProjectData(parseInt(projectId));
        }
    }, [projectId]);

    async function loadProjectData(pid: number) {
        try {
            setLoading(true);
            const [projectData, scenesData] = await Promise.all([
                getProject(pid),
                getScenes(pid),
            ]);
            setProject(projectData);
            setScenes(scenesData.scenes);
            if (scenesData.scenes.length > 0) {
                setSelectedSceneId(scenesData.scenes[0].id);
            }
        } catch (error) {
            toast.error('Failed to load project');
        } finally {
            setLoading(false);
        }
    }

    const selectedScene = scenes.find(s => s.id === selectedSceneId) || null;

    async function handleRebuildVideo() {
        if (!project) return;
        setIsRebuilding(true);
        try {
            toast.loading('Rebuilding video with updated scenes...', { id: 'rebuild' });
            const result = await buildVideo(project.id);
            setProject({ ...project, final_video_url: result.final_video, status: 'completed' });
            toast.success('Video rebuilt successfully!', { id: 'rebuild' });
            // Refresh scenes to get latest URLs
            const scenesData = await getScenes(project.id);
            setScenes(scenesData.scenes);
        } catch (error) {
            toast.error('Failed to rebuild video', { id: 'rebuild' });
        } finally {
            setIsRebuilding(false);
        }
    }

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
                    <p className="text-dark-200">Loading project...</p>
                </div>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="glass-card p-8 text-center">
                    <p className="text-xl text-dark-200 mb-4">No project loaded</p>
                    <a href="/" className="btn-primary inline-block">← Back to Upload</a>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen px-4 py-6 max-w-[1600px] mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-white">{project.title}</h1>
                    <p className="text-sm text-dark-200 mt-1">
                        {scenes.length} scenes •{' '}
                        <span className={`${project.status === 'completed' ? 'text-accent-green' : 'text-accent-orange'}`}>
                            {project.status}
                        </span>
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRebuildVideo}
                        disabled={isRebuilding}
                        className="btn-secondary flex items-center gap-2"
                    >
                        {isRebuilding ? (
                            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : '🔄'}
                        Rebuild Video
                    </button>
                    {project.final_video_url && (
                        <a
                            href={getExportUrl(project.id)}
                            download
                            className="btn-primary flex items-center gap-2"
                        >
                            📥 Export MP4
                        </a>
                    )}
                </div>
            </div>

            {/* Main Layout: 3 columns */}
            <div className="grid grid-cols-12 gap-4">
                {/* Video Preview */}
                <div className="col-span-12 lg:col-span-7">
                    <VideoPreview
                        videoUrl={project.final_video_url}
                        scene={selectedScene}
                    />
                </div>

                {/* Right Panel */}
                <div className="col-span-12 lg:col-span-5">
                    {/* Panel Tabs */}
                    <div className="flex gap-2 mb-3">
                        {[
                            { key: 'editor', label: '✏️ Edit Scene', id: 'editor-tab' },
                            { key: 'explain', label: '🔍 Explainability', id: 'explain-tab' },
                            { key: 'versions', label: '📋 Versions', id: 'versions-tab' },
                        ].map((tab) => (
                            <button
                                key={tab.key}
                                id={tab.id}
                                onClick={() => setActivePanel(tab.key as any)}
                                className={`flex-1 py-2 rounded-xl text-xs font-medium transition-all ${activePanel === tab.key
                                        ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                                        : 'bg-dark-600 text-dark-200 border border-transparent'
                                    }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Panel Content */}
                    <div className="glass-card p-5 min-h-[400px]">
                        {selectedScene ? (
                            <>
                                {activePanel === 'editor' && (
                                    <SceneEditor
                                        scene={selectedScene}
                                        onUpdate={async () => {
                                            if (project) {
                                                const scenesData = await getScenes(project.id);
                                                setScenes(scenesData.scenes);
                                            }
                                        }}
                                    />
                                )}
                                {activePanel === 'explain' && (
                                    <ExplainabilityPanel scene={selectedScene} />
                                )}
                                {activePanel === 'versions' && (
                                    <VersionHistory
                                        scene={selectedScene}
                                        onRevert={async () => {
                                            if (project) {
                                                const scenesData = await getScenes(project.id);
                                                setScenes(scenesData.scenes);
                                            }
                                        }}
                                    />
                                )}
                            </>
                        ) : (
                            <div className="flex items-center justify-center h-full">
                                <p className="text-dark-300">Select a scene from the timeline below</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Timeline */}
            <div className="mt-4">
                <SceneTimeline
                    scenes={scenes}
                    selectedSceneId={selectedSceneId}
                    onSelectScene={setSelectedSceneId}
                />
            </div>
        </div>
    );
}
