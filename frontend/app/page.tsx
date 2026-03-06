'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from '@/lib/store';
import { uploadContent, generateScript, generateScenes, generateVisuals, generateVoice, buildVideo } from '@/lib/api';
import UploadZone from '@/components/upload/UploadZone';
import toast from 'react-hot-toast';

const PIPELINE_STEPS = [
    { label: 'Upload Content', icon: '📄' },
    { label: 'Generate Script', icon: '✍️' },
    { label: 'Create Scenes', icon: '🎬' },
    { label: 'Generate Visuals', icon: '🎨' },
    { label: 'Generate Voice', icon: '🎙️' },
    { label: 'Build Video', icon: '🎥' },
];

export default function HomePage() {
    const router = useRouter();
    const { setProject, setScenes, setScriptData, setPipelineStep, pipelineStep } = useStore();
    const [file, setFile] = useState<File | null>(null);
    const [textContent, setTextContent] = useState('');
    const [title, setTitle] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [mode, setMode] = useState<'upload' | 'paste'>('upload');

    const handleProcess = useCallback(async () => {
        if (!file && !textContent.trim()) {
            toast.error('Please upload a file or paste content');
            return;
        }

        setIsProcessing(true);

        try {
            // Step 1: Upload
            setCurrentStep(1);
            toast.loading('Uploading content...', { id: 'pipeline' });
            const uploadResult = await uploadContent(file || undefined, textContent || undefined, title || undefined);
            const projectId = uploadResult.project_id;
            setProject({ id: projectId, title: uploadResult.title, status: 'created', final_video_url: null, content_preview: uploadResult.content_preview });

            // Step 2: Generate Script
            setCurrentStep(2);
            toast.loading('Generating script with AI...', { id: 'pipeline' });
            const scriptResult = await generateScript(projectId);
            setScriptData(scriptResult.script);

            // Step 3: Create Scenes
            setCurrentStep(3);
            toast.loading('Creating scenes...', { id: 'pipeline' });
            const scenesResult = await generateScenes(projectId, scriptResult.script);
            setScenes(scenesResult.scenes);

            // Step 4: Generate Visuals
            setCurrentStep(4);
            toast.loading('Generating visuals...', { id: 'pipeline' });
            await generateVisuals(projectId);

            // Step 5: Generate Voice
            setCurrentStep(5);
            toast.loading('Generating voiceovers...', { id: 'pipeline' });
            await generateVoice(projectId);

            // Step 6: Build Video
            setCurrentStep(6);
            toast.loading('Building video...', { id: 'pipeline' });
            await buildVideo(projectId);

            toast.success('Video generated! Redirecting to editor...', { id: 'pipeline' });
            setPipelineStep(6);

            // Navigate to editor
            setTimeout(() => router.push(`/editor?project=${projectId}`), 1000);

        } catch (error: any) {
            console.error('Pipeline error:', error);
            toast.error(error?.response?.data?.detail || 'Something went wrong', { id: 'pipeline' });
        } finally {
            setIsProcessing(false);
        }
    }, [file, textContent, title, router, setProject, setScenes, setScriptData, setPipelineStep]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
            {/* Hero */}
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
                <p className="text-lg text-dark-200 max-w-xl mx-auto">
                    Upload research papers, lecture notes, or reports. Our AI agents will convert them into editable, scene-based videos in minutes.
                </p>
            </div>

            {/* Pipeline Progress */}
            {isProcessing && (
                <div className="w-full max-w-2xl mb-8">
                    <div className="glass-card p-6">
                        <div className="flex items-center justify-between mb-4">
                            {PIPELINE_STEPS.map((step, i) => (
                                <div key={i} className="flex flex-col items-center gap-1">
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg transition-all duration-500 ${i + 1 < currentStep ? 'bg-accent-green/20 text-accent-green' :
                                            i + 1 === currentStep ? 'bg-primary-500/20 text-primary-400 animate-pulse-slow glow' :
                                                'bg-dark-600 text-dark-300'
                                        }`}>
                                        {i + 1 < currentStep ? '✓' : step.icon}
                                    </div>
                                    <span className={`text-[10px] ${i + 1 <= currentStep ? 'text-dark-100' : 'text-dark-300'}`}>
                                        {step.label}
                                    </span>
                                </div>
                            ))}
                        </div>
                        <div className="w-full bg-dark-600 rounded-full h-2">
                            <div
                                className="h-2 rounded-full bg-gradient-to-r from-primary-500 via-accent-cyan to-accent-purple transition-all duration-1000"
                                style={{ width: `${(currentStep / PIPELINE_STEPS.length) * 100}%` }}
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Upload Card */}
            <div className="glass-card p-8 w-full max-w-2xl glow">
                {/* Mode Tabs */}
                <div className="flex gap-2 mb-6">
                    <button
                        onClick={() => setMode('upload')}
                        className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${mode === 'upload'
                                ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                                : 'bg-dark-600 text-dark-200 border border-transparent hover:bg-dark-500'
                            }`}
                    >
                        📁 Upload File
                    </button>
                    <button
                        onClick={() => setMode('paste')}
                        className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${mode === 'paste'
                                ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                                : 'bg-dark-600 text-dark-200 border border-transparent hover:bg-dark-500'
                            }`}
                    >
                        📝 Paste Text
                    </button>
                </div>

                {/* Title Input */}
                <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Project title (optional)"
                    className="w-full bg-dark-700 border border-dark-400 rounded-xl px-4 py-3 text-white placeholder:text-dark-300 focus:outline-none focus:border-primary-500 mb-4 transition-colors"
                />

                {/* Upload or Paste */}
                {mode === 'upload' ? (
                    <UploadZone onFileSelect={setFile} selectedFile={file} />
                ) : (
                    <textarea
                        value={textContent}
                        onChange={(e) => setTextContent(e.target.value)}
                        placeholder="Paste your content here... (research paper, lecture notes, report, etc.)"
                        rows={8}
                        className="w-full bg-dark-700 border border-dark-400 rounded-xl px-4 py-3 text-white placeholder:text-dark-300 focus:outline-none focus:border-primary-500 resize-none transition-colors"
                    />
                )}

                {/* Generate Button */}
                <button
                    onClick={handleProcess}
                    disabled={isProcessing || (!file && !textContent.trim())}
                    className="w-full mt-6 btn-primary text-lg py-4 flex items-center justify-center gap-3"
                >
                    {isProcessing ? (
                        <>
                            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            Processing...
                        </>
                    ) : (
                        <>
                            🚀 Generate Video
                        </>
                    )}
                </button>
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-12 max-w-4xl w-full">
                {[
                    { icon: '🤖', title: 'Multi-Agent AI', desc: 'Script, Visual, Voice, and Fact-Check agents work together' },
                    { icon: '🎬', title: 'Scene Editing', desc: 'Edit individual scenes without regenerating the whole video' },
                    { icon: '🔍', title: 'Explainability', desc: 'See source references and AI confidence for every scene' },
                ].map((f, i) => (
                    <div key={i} className="glass-card p-5 text-center hover:border-primary-500/30 transition-all group">
                        <div className="text-3xl mb-2 group-hover:scale-110 transition-transform">{f.icon}</div>
                        <h3 className="font-semibold text-white mb-1">{f.title}</h3>
                        <p className="text-sm text-dark-200">{f.desc}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}
