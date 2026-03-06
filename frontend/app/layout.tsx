import type { Metadata } from 'next';
import './globals.css';
import { Toaster } from 'react-hot-toast';

export const metadata: Metadata = {
    title: 'StoryHack — Agentic Video Editor',
    description: 'AI-powered platform to convert research papers, lecture notes, and reports into editable videos with scene-level editing.',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className="antialiased">
                <Toaster
                    position="top-right"
                    toastOptions={{
                        style: {
                            background: '#1a1b1e',
                            color: '#e4e4e7',
                            border: '1px solid rgba(255,255,255,0.1)',
                        },
                    }}
                />
                <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-b border-white/5 px-6 py-4">
                    <div className="max-w-7xl mx-auto flex items-center justify-between">
                        <a href="/" className="flex items-center gap-3 group">
                            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-accent-cyan flex items-center justify-center text-white font-bold text-lg group-hover:shadow-lg group-hover:shadow-primary-500/30 transition-all">
                                S
                            </div>
                            <span className="text-xl font-bold gradient-text">StoryHack</span>
                        </a>
                        <div className="flex items-center gap-4">
                            <span className="text-xs text-dark-200 bg-dark-600 px-3 py-1 rounded-full">
                                Agentic Edits
                            </span>
                        </div>
                    </div>
                </nav>
                <main className="pt-20 min-h-screen">
                    {children}
                </main>
            </body>
        </html>
    );
}
