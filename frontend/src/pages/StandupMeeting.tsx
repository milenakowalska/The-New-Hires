import { useState, useRef, useEffect } from 'react';
import { Mic, Play, Square, User as UserIcon, Loader } from 'lucide-react';
import api from '../api/client';

export default function StandupMeeting() {
    const [step, setStep] = useState<'waiting' | 'coworker' | 'user' | 'done'>('waiting');
    const [coworker, setCoworker] = useState<{ name: string, role: string, text: string, audio_url: string } | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [coworkerRound, setCoworkerRound] = useState(0);
    const [audioError, setAudioError] = useState(false);

    const audioRef = useRef<HTMLAudioElement>(null);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);

    const startMeeting = () => {
        setStep('coworker');
        fetchCoworkerUpdate();
    };

    const fetchCoworkerUpdate = async () => {
        try {
            console.log("DEBUG: Fetching from V2 endpoint...");
            const res = await api.get('/features/standups/daily-update-v2');
            setCoworker(res.data);
            setAudioError(false);
        } catch (error) {
            console.error("Failed to fetch coworker", error);
        }
    };

    const handleCoworkerAudioEnded = () => {
        if (coworkerRound < 1) {
            setCoworkerRound(prev => prev + 1);
            setCoworker(null);
            fetchCoworkerUpdate();
        } else {
            setStep('user');
        }
    };

    useEffect(() => {
        if (coworker && audioRef.current) {
            // Reset error state when new coworker loads, but avoid direct state update if possible
            // We can just rely on the key prop or similar if we wanted to force reload
            audioRef.current.play().catch(err => {
                console.error("Audio play failed:", err);
                setAudioError(true);
            });
        }
    }, [coworker]);

    const handleAudioError = () => {
        console.error("Audio failed to load");
        setAudioError(true);
    };

    const skipCoworker = () => {
        handleCoworkerAudioEnded();
    };

    const startRecording = async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;

        const chunks: BlobPart[] = [];
        mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
        mediaRecorder.onstop = () => {
            const blob = new Blob(chunks, { type: 'audio/webm' });
            // setAudioBlob(blob); // Unused
            uploadStandup(blob);
        };

        mediaRecorder.start();
        setIsRecording(true);
    };

    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
        setIsRecording(false);
    };

    const uploadStandup = async (blob: Blob) => {
        const formData = new FormData();
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        formData.append('file', blob, 'standup.webm');

        try {
            const res = await api.post(`/features/standups/upload?user_id=${user.id}`, formData);
            setTranscript(res.data.transcript);
            setStep('done');
        } catch (error) {
            console.error("Upload failed", error);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center h-full p-6 text-center">
            {step === 'waiting' && (
                <div className="space-y-6">
                    <h1 className="text-3xl font-bold text-white">Morning Standup</h1>
                    <p className="text-gray-400">Join the daily meeting with your AI coworkers.</p>
                    <button
                        onClick={startMeeting}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-full text-lg transition-transform hover:scale-105"
                    >
                        Join Meeting
                    </button>
                </div>
            )}

            {step === 'coworker' && coworker && (
                <div className="space-y-8 animate-fade-in">
                    <div className="w-32 h-32 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center mx-auto shadow-2xl relative">
                        <UserIcon className="w-16 h-16 text-white" />
                        <div className="absolute inset-0 rounded-full border-4 border-white/20 animate-pulse"></div>
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-white">{coworker.name}</h2>
                        <p className="text-indigo-400">{coworker.role}</p>
                    </div>
                    <div className="bg-gray-800/50 p-6 rounded-xl max-w-lg mx-auto border border-gray-700">
                        <p className="text-gray-300 italic">"{coworker.text}"</p>
                    </div>

                    {audioError && (
                        <div className="text-rose-400 text-sm">
                            Audio failed to load. Click "Skip" to continue.
                        </div>
                    )}

                    <button
                        onClick={skipCoworker}
                        className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded-lg text-sm transition-colors"
                    >
                        Skip →
                    </button>

                    <audio
                        ref={audioRef}
                        src={coworker.audio_url}
                        onEnded={handleCoworkerAudioEnded}
                        onError={handleAudioError}
                        className="hidden"
                    />
                </div>
            )}

            {step === 'coworker' && !coworker && (
                <div className="flex flex-col items-center justify-center space-y-4">
                    <Loader className="w-10 h-10 text-blue-500 animate-spin" />
                    <p className="text-gray-400">Waiting for next speaker...</p>
                </div>
            )}

            {step === 'user' && (
                <div className="space-y-8">
                    <div className="w-32 h-32 rounded-full bg-gray-800 border-4 border-gray-700 flex items-center justify-center mx-auto relative overflow-hidden">
                        {isRecording && <div className="absolute inset-0 bg-red-500/20 animate-ping rounded-full"></div>}
                        <div className="z-10 bg-gray-900 rounded-full p-4">
                            <Mic className={`w-12 h-12 ${isRecording ? 'text-red-500' : 'text-gray-400'}`} />
                        </div>
                    </div>

                    <h2 className="text-2xl font-bold text-white">Your Turn</h2>
                    <p className="text-gray-400">Tell us what you did yesterday and what you're doing today.</p>

                    {!isRecording ? (
                        <button
                            onClick={startRecording}
                            className="bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-8 rounded-full flex items-center justify-center mx-auto space-x-2 transition-all"
                        >
                            <Mic className="w-6 h-6" />
                            <span>Start Speaking</span>
                        </button>
                    ) : (
                        <button
                            onClick={stopRecording}
                            className="bg-gray-700 hover:bg-gray-600 text-white font-bold py-4 px-8 rounded-full flex items-center justify-center mx-auto space-x-2 border border-red-500 transition-all"
                        >
                            <Square className="w-6 h-6 fill-current text-red-500" />
                            <span>Stop & Submit</span>
                        </button>
                    )}
                </div>
            )}

            {step === 'done' && (
                <div className="space-y-6">
                    <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
                        <Play className="w-10 h-10 text-green-500 fill-current" />
                    </div>
                    <h2 className="text-2xl font-bold text-white">Standup Completed!</h2>
                    <div className="bg-gray-800 p-6 rounded-xl max-w-lg mx-auto text-left">
                        <h3 className="text-sm font-bold text-gray-500 uppercase mb-2">Transcript Analysis</h3>
                        <p className="text-gray-300">{transcript}</p>
                    </div>
                    <p className="text-blue-400">Truthfulness Score Updated.</p>

                    <button
                        onClick={() => window.location.reload()}
                        className="text-gray-400 hover:text-white underline"
                    >
                        Leave Meeting
                    </button>
                </div>
            )}
        </div>
    );
}
