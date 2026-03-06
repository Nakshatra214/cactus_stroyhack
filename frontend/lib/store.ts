/**
 * Zustand Store — Global state management for StoryHack
 */
import { create } from 'zustand';

export interface Scene {
    id: number;
    scene_index: number;
    scene_title: string;
    script: string;
    visual_prompt: string;
    visual_description: string;
    camera_shot: string;
    animation_type: string;
    motion_direction: string;
    visual_layers: string[];
    text_overlay: string;
    transition: string;
    image_url: string | null;
    audio_url: string | null;
    video_clip: string | null;
    source_reference: string;
    confidence_score: number;
    version: number;
    duration: number;
    voice_tone: string;
    status: string;
}

export interface Project {
    id: number;
    title: string;
    status: string;
    final_video_url: string | null;
    content_preview: string;
}

interface StoryHackState {
    // Project
    project: Project | null;
    setProject: (project: Project | null) => void;

    // Scenes
    scenes: Scene[];
    setScenes: (scenes: Scene[]) => void;
    updateScene: (sceneId: number, updates: Partial<Scene>) => void;

    // Selected scene
    selectedSceneId: number | null;
    setSelectedSceneId: (id: number | null) => void;

    // Script data
    scriptData: any | null;
    setScriptData: (data: any) => void;

    // UI state
    isLoading: boolean;
    setLoading: (loading: boolean) => void;
    loadingStep: string;
    setLoadingStep: (step: string) => void;

    // Pipeline step tracking
    pipelineStep: number;
    setPipelineStep: (step: number) => void;
}

export const useStore = create<StoryHackState>((set) => ({
    project: null,
    setProject: (project) => set({ project }),

    scenes: [],
    setScenes: (scenes) => set({ scenes }),
    updateScene: (sceneId, updates) =>
        set((state) => ({
            scenes: state.scenes.map((s) =>
                s.id === sceneId ? { ...s, ...updates } : s
            ),
        })),

    selectedSceneId: null,
    setSelectedSceneId: (id) => set({ selectedSceneId: id }),

    scriptData: null,
    setScriptData: (data) => set({ scriptData: data }),

    isLoading: false,
    setLoading: (loading) => set({ isLoading: loading }),
    loadingStep: '',
    setLoadingStep: (step) => set({ loadingStep: step }),

    pipelineStep: 0,
    setPipelineStep: (step) => set({ pipelineStep: step }),
}));
