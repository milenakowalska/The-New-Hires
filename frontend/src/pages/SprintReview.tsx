import { useState, useEffect } from 'react';
import api from '../api/client';

export default function SprintReview() {
    const [file, setFile] = useState<File | null>(null);
    const [analyzing, setAnalyzing] = useState(false);
    const [report, setReport] = useState<string | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [duration, setDuration] = useState<string | null>(null);
    const [history, setHistory] = useState<{ date: string, report: string }[]>([]);

    const fetchHistory = async () => {
        try {
            const userJson = localStorage.getItem('user');
            const userData = userJson ? JSON.parse(userJson) : { id: 1 };
            const response = await api.get(`/features/sprint-review/history?user_id=${userData.id}`);
            setHistory(response.data);
        } catch (error) {
            console.error("Failed to fetch history:", error);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            setReport(null);

            const video = document.createElement('video');
            video.preload = 'metadata';
            video.onloadedmetadata = () => {
                window.URL.revokeObjectURL(video.src);
                const minutes = Math.floor(video.duration / 60);
                const seconds = Math.floor(video.duration % 60);
                setDuration(`${minutes}:${seconds.toString().padStart(2, '0')}`);
            };
            video.src = URL.createObjectURL(selectedFile);
        }
    };

    const handleAnalyze = async () => {
        if (!file) return;

        setAnalyzing(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const userJson = localStorage.getItem('user');
            const userData = userJson ? JSON.parse(userJson) : { id: 1 };

            const url = `/features/sprint-review/analyze?user_id=${userData.id}${duration ? `&duration=${duration}` : ''}`;
            const response = await api.post(url, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setReport(response.data.report);
            fetchHistory();
        } catch (error) {
            console.error("Analysis failed:", error);
            alert("Failed to analyze video. Please try again.");
        } finally {
            setAnalyzing(false);
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
            setReport(null);
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <header className="mb-8">
                <h2 className="text-3xl font-bold text-slate-900 mb-2">Sprint Review</h2>
                <p className="text-slate-600">
                    Upload your sprint review recording for AI analysis and reporting.
                </p>
            </header>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                <div className="mb-8">
                    <h3 className="text-lg font-semibold text-slate-800 mb-4">Instructions</h3>
                    <ul className="space-y-3 text-slate-600">
                        <li className="flex items-start gap-3">
                            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">1</span>
                            <span>Record a video showing key features you implemented this sprint.</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">2</span>
                            <span>Ensure the video is in .mp4, .mov, or .webm format and under 3 minutes.</span>
                        </li>
                        <li className="flex items-start gap-3">
                            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">3</span>
                            <span>Upload the file below to generate your sprint review report.</span>
                        </li>
                    </ul>
                </div>

                <div
                    className={`flex flex-col items-center justify-center py-12 border-2 border-dashed rounded-lg transition-colors ${dragActive ? 'border-blue-400 bg-blue-50' : 'border-slate-200 bg-slate-50'
                        }`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    {!file && !analyzing && (
                        <div className="text-center">
                            <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 3 3m-3-3v15" />
                                </svg>
                            </div>
                            <h4 className="text-lg font-medium text-slate-900 mb-2">Select your review video</h4>
                            <p className="text-slate-500 mb-6">Drag and drop or click to browse (.mp4, .mov, .webm)</p>
                            <input
                                type="file"
                                accept="video/mp4,video/quicktime,video/webm"
                                onChange={handleFileChange}
                                className="hidden"
                                id="video-upload"
                            />
                            <label
                                htmlFor="video-upload"
                                className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm cursor-pointer inline-block"
                            >
                                Choose File
                            </label>
                        </div>
                    )}

                    {file && !report && (
                        <div className="text-center w-full">
                            {analyzing ? (
                                <div className="py-8">
                                    <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                                    <h4 className="text-lg font-medium text-slate-900 mb-1">Gemini is analyzing video...</h4>
                                    <p className="text-slate-500">This may take a minute.</p>
                                </div>
                            ) : (
                                <>
                                    <div className="w-16 h-16 bg-amber-50 text-amber-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
                                        </svg>
                                    </div>
                                    <h4 className="text-lg font-medium text-slate-900 mb-1">{file.name}</h4>
                                    <p className="text-slate-500 mb-6">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                                </>
                            )}

                            <div className="flex gap-4 justify-center">
                                <button
                                    onClick={() => setFile(null)}
                                    disabled={analyzing}
                                    className="px-6 py-3 bg-white border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors shadow-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleAnalyze}
                                    disabled={analyzing}
                                    className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-slate-400 disabled:cursor-not-allowed transition-colors shadow-sm flex items-center gap-2"
                                >
                                    {analyzing && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                                    {analyzing ? 'Analyzing...' : 'Analyze Review'}
                                </button>
                            </div>
                        </div>
                    )}

                    {report && (
                        <div className="w-full px-4">
                            <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-emerald-500">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                                </svg>
                                Sprint Review Report
                            </h4>
                            <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-6 text-emerald-900 font-mono text-sm leading-relaxed">
                                {report}
                            </div>
                            <div className="mt-8 flex justify-center">
                                <button
                                    onClick={() => { setFile(null); setReport(null); }}
                                    className="px-6 py-3 bg-white border border-slate-300 text-slate-700 font-semibold rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
                                >
                                    Upload New Video
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {history.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8">
                    <h3 className="text-xl font-bold text-slate-900 mb-6">Submission History</h3>
                    <div className="space-y-4">
                        {history.map((item, index) => (
                            <div key={index} className="border-l-4 border-blue-500 bg-slate-50 p-4 rounded-r-lg">
                                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                    {new Date(item.date).toLocaleDateString()} {new Date(item.date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </div>
                                <p className="text-slate-700 font-mono text-sm leading-relaxed">
                                    {item.report}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
