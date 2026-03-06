/**
 * API Client — Backend communication layer
 */
import axios from 'axios';

const api = axios.create({
    baseURL: '/api',
    timeout: 600000, // 2 minutes for video generation
});

// Upload
export async function uploadContent(file?: File, textContent?: string, title?: string) {
    const formData = new FormData();
    if (file) formData.append('file', file);
    if (textContent) formData.append('text_content', textContent);
    if (title) formData.append('title', title);
    const { data } = await api.post('/upload_content', formData);
    return data;
}

// Script
export async function generateScript(projectId: number) {
    const { data } = await api.post('/generate_script', { project_id: projectId });
    return data;
}

// Scenes
export async function generateScenes(projectId: number, script: any) {
    const { data } = await api.post('/generate_scenes', { project_id: projectId, script });
    return data;
}

export async function getScenes(projectId: number) {
    const { data } = await api.get(`/scenes/${projectId}`);
    return data;
}

export async function editScene(sceneId: number, updates: any) {
    const { data } = await api.post('/edit_scene', { scene_id: sceneId, ...updates });
    return data;
}

export async function regenerateScene(sceneId: number) {
    const { data } = await api.post('/regenerate_scene', { scene_id: sceneId });
    return data;
}

export async function getSceneVersions(sceneId: number) {
    const { data } = await api.get(`/scene_versions/${sceneId}`);
    return data;
}

export async function revertScene(sceneId: number, version: number) {
    const { data } = await api.post('/revert_scene', { scene_id: sceneId, version });
    return data;
}

export async function reorderScenes(projectId: number, sceneOrder: number[]) {
    const { data } = await api.post('/reorder_scenes', { project_id: projectId, scene_order: sceneOrder });
    return data;
}

// Video
export async function generateVisuals(projectId: number) {
    const { data } = await api.post('/generate_visuals', { project_id: projectId });
    return data;
}

export async function generateVoice(projectId: number) {
    const { data } = await api.post('/generate_voice', { project_id: projectId });
    return data;
}

export async function buildVideo(projectId: number) {
    const { data } = await api.post('/build_video', { project_id: projectId });
    return data;
}

export async function processVideoAsync(projectId: number) {
    const { data } = await api.post('/process_video_async', { project_id: projectId });
    return data;
}

export async function getProject(projectId: number) {
    const { data } = await api.get(`/project/${projectId}`);
    return data;
}

export function getExportUrl(projectId: number, format: string = 'mp4') {
    return `/api/export_video/${projectId}?format=${format}`;
}

export function getExportAssetsUrl(projectId: number) {
    return `/api/export_assets/${projectId}`;
}
