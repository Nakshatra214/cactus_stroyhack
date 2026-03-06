'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from '@/lib/store';
import { uploadContent, processVideoAsync, getProject } from '@/lib/api';
import UploadZone from '@/components/upload/UploadZone';
import toast from 'react-hot-toast';

const PIPELINE_STEPS = [
    { label: 'Upload Content', icon: '📄', status: 'created' },
    { label: 'Generate Script', icon: '✍️', status: 'processing' },
    { label: 'Create Scenes', icon: '🎬', status: 'scripted' },
    { label: 'Generate Visuals', icon: '🎨', status: 'visual_done' },
    { label: 'Generate Voice', icon: '🎙️', status: 'voice_done' },
    { label: 'Build Video', icon: '🎥', status: 'completed' },
];

export default function HomePage() {
    const router = useRouter();
    const { setProject, setPipelineStep } = useStore();
    const [file, setFile] = useState<File | null>(null);
    const [textContent, setTextContent] = useState('');
    const [title, setTitle] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [mode, setMode] = useState<'upload' | 'paste'>('upload');

    const pollStatus = async (projectId: number) => {
        const checkStatus = async () => {
            try {
                const project = await getProject(projectId);

                // Update current step based on backend status
                if (project.status === 'processing') setCurrentStep(2);
                else if (project.status === 'scripted') setCurrentStep(3);
                else if (project.status === 'visual_done') setCurrentStep(4);
                else if (project.status === 'voice_done') setCurrentStep(5);
                else if (project.status === 'completed') {
                    setCurrentStep(6);
                    toast.success('Video ready!', { id: 'pipeline' });
                    setTimeout(() => router.push(`/editor?project=${projectId}`), 1500);
                    return true;
                }
                return false;
            } catch (e) {
                console.error('Polling error:', e);
                return false;
            }
        };

        const interval = setInterval(async () => {
            const finished = await checkStatus();
            if (finished) clearInterval(interval);
        }, 3000);
    };

    const handleProcess = useCallback(async () => {
        if (!file && !textContent.trim()) {
            toast.error('Please upload content');
            return;
        }

        setIsProcessing(true);
        setCurrentStep(1);
        toast.loading('Starting generation...', { id: 'pipeline' });

        try {
            // Upload first (Synchronous but fast)
            const uploadResult = await uploadContent(file || undefined, textContent || undefined, title || undefined);
            const projectId = uploadResult.project_id;
            setProject({
                id: projectId,
                title: uploadResult.title,
                status: uploadResult.status || 'created',
                final_video_url: null,
                content_preview: uploadResult.content_preview || '',
            });

            // Trigger background pipeline
            await processVideoAsync(projectId);
            toast.loading('AI agents are working in the background...', { id: 'pipeline' });

            // Start polling
            pollStatus(projectId);

        } catch (error: any) {
            console.error('Process error:', error);
            toast.error('Failed to start processing', { id: 'pipeline' });
            setIsProcessing(false);
        }
    }, [file, textContent, title, setProject]);

    useEffect(() => {
        if (file && !isProcessing) handleProcess();
    }, [file, isProcessing, handleProcess]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
            <div className="text-center mb-12 max-w-3xl">
                <div className="inline-flex items-center gap-2 bg-dark-600/50 border border-dark-400 rounded-full px-4 py-1.5 mb-6">
                    <span className="w-2 h-2 bg-accent-cyan rounded-full animate-pulse" />
                    <span className="text-sm text-dark-100">Powered by Multi-Agent AI</span>
                </div>
                <h1 className="text-5xl md:text-6xl font-extrabold mb-4">
                    <span className="gradient-text">Turn Content</span>
                    <br />
                    <span className="text-white">Into Videos</span>
                </h1>
                <p className="text-lg text-dark-200">Our AI agents will convert your documents into animated videos automatically.</p>
            </div>

            {isProcessing && (
                <div className="w-full max-w-2xl mb-8">
                    <div className="glass-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            {PIPELINE_STEPS.map((step, i) => (
                                <div key={i} className="flex flex-col items-center gap-1">
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${i + 1 < currentStep ? 'bg-accent-green/20 text-accent-green' : i + 1 === currentStep ? 'bg-primary-500/20 text-primary-400 animate-pulse glow' : 'bg-dark-600 text-dark-300'}`}>
                                        {i + 1 < currentStep ? '✓' : step.icon}
                                    </div>
                                    <span className="text-[10px] text-dark-200">{step.label}</span>
                                </div>
                            ))}
                        </div>
                        <div className="w-full bg-dark-600 rounded-full h-2">
                            <div className="h-2 rounded-full bg-primary-500 transition-all duration-1000" style={{ width: `${(currentStep / 6) * 100}%` }} />
                        </div>
                    </div>
                </div>
            )}

            <div className="glass-card p-8 w-full max-w-2xl">
                <div className="flex gap-2 mb-6">
                    <button onClick={() => setMode('upload')} className={`flex-1 py-2 rounded-xl ${mode === 'upload' ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30' : 'bg-dark-600'}`}>📁 Upload File</button>
                    <button onClick={() => setMode('paste')} className={`flex-1 py-2 rounded-xl ${mode === 'paste' ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30' : 'bg-dark-600'}`}>📝 Paste Text</button>
                </div>
                <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Project title" className="w-full bg-dark-700 border border-dark-400 rounded-xl px-4 py-3 mb-4" />
                {mode === 'upload' ? <UploadZone onFileSelect={setFile} selectedFile={file} /> : <textarea value={textContent} onChange={(e) => setTextContent(e.target.value)} placeholder="Paste content..." rows={8} className="w-full bg-dark-700 border border-dark-400 rounded-xl px-4 py-3 resize-none" />}
                <button onClick={handleProcess} disabled={isProcessing} className="w-full mt-6 btn-primary py-4">{isProcessing ? 'Agent Working...' : '🚀 Generate Video'}</button>
            </div>
        </div>
    );
}
