'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface UploadZoneProps {
    onFileSelect: (file: File) => void;
    selectedFile: File | null;
}

export default function UploadZone({ onFileSelect, selectedFile }: UploadZoneProps) {
    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            onFileSelect(acceptedFiles[0]);
        }
    }, [onFileSelect]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/plain': ['.txt'],
            'text/markdown': ['.md'],
        },
        maxFiles: 1,
        maxSize: 50 * 1024 * 1024, // 50MB
    });

    return (
        <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${isDragActive
                    ? 'border-primary-400 bg-primary-500/10'
                    : selectedFile
                        ? 'border-accent-green/50 bg-accent-green/5'
                        : 'border-dark-400 hover:border-primary-500/50 hover:bg-dark-600/50'
                }`}
        >
            <input {...getInputProps()} />
            {selectedFile ? (
                <div className="flex flex-col items-center gap-2">
                    <div className="w-12 h-12 rounded-xl bg-accent-green/20 flex items-center justify-center text-2xl">
                        ✅
                    </div>
                    <p className="text-white font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-dark-200">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Click or drop to replace
                    </p>
                </div>
            ) : (
                <div className="flex flex-col items-center gap-3">
                    <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-3xl transition-all ${isDragActive ? 'bg-primary-500/20 scale-110' : 'bg-dark-600'
                        }`}>
                        {isDragActive ? '📥' : '📄'}
                    </div>
                    <div>
                        <p className="text-white font-medium">
                            {isDragActive ? 'Drop it here!' : 'Drag & drop your file here'}
                        </p>
                        <p className="text-sm text-dark-300 mt-1">
                            PDF, DOCX, TXT, or Markdown • Max 50MB
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
