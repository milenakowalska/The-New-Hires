import { useState, useEffect } from 'react';
import { TrendingUp, CheckCircle, Clock, Target, Award, ThumbsUp, ThumbsDown, PartyPopper } from 'lucide-react';
import api from '../api/client';
import { useNavigate } from 'react-router-dom';

interface SprintStats {
    user: {
        username: string;
        avatar_url: string;
        level: number;
        xp: number;
    };
    metrics: {
        truthfulness: number;
        effort: number;
        reliability: number;
        collaboration: number;
        quality: number;
    };
    tickets: {
        total: number;
        completed: number;
        in_progress: number;
        todo: number;
        completion_rate: number;
    };
    story_points: {
        total: number;
        completed: number;
    };
    standups_completed: number;
    sprint_days: number;
}

export default function Retrospective() {
    const [step, setStep] = useState<'dashboard' | 'feedback' | 'done'>('dashboard');
    const [stats, setStats] = useState<SprintStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [wentWell, setWentWell] = useState('');
    const [toImprove, setToImprove] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        fetchSprintStats();
    }, []);

    const fetchSprintStats = async () => {
        try {
            const userJson = localStorage.getItem('user');
            if (!userJson) return;
            const user = JSON.parse(userJson);
            const res = await api.get(`/features/retrospectives/sprint-stats?user_id=${user.id}`);
            setStats(res.data);
        } catch (error) {
            console.error("Failed to fetch sprint stats", error);
        } finally {
            setLoading(false);
        }
    };

    const submitFeedback = () => {
        // In a real app, you'd save this feedback to the backend
        console.log("Feedback submitted:", { wentWell, toImprove });
        setStep('done');
    };

    const getMetricColor = (value: number) => {
        if (value >= 70) return 'text-green-400';
        if (value >= 40) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getMetricBg = (value: number) => {
        if (value >= 70) return 'bg-green-500';
        if (value >= 40) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    if (loading) {
        return <div className="flex items-center justify-center h-full text-white">Loading sprint data...</div>;
    }

    return (
        <div className="max-w-6xl mx-auto p-6">
            {/* DASHBOARD STEP */}
            {step === 'dashboard' && stats && (
                <div className="space-y-8 animate-fade-in">
                    <div className="text-center mb-8">
                        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                            Sprint Retrospective
                        </h1>
                        <p className="text-gray-300 mt-2">Review your {stats.sprint_days}-day sprint performance</p>
                    </div>

                    {/* User Card */}
                    <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 rounded-2xl p-6 border border-purple-500/30">
                        <div className="flex items-center gap-4">
                            {stats.user.avatar_url ? (
                                <img src={stats.user.avatar_url} alt={stats.user.username} className="w-16 h-16 rounded-full" />
                            ) : (
                                <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-purple-500 to-pink-500 flex items-center justify-center text-white text-2xl font-bold">
                                    {stats.user.username?.charAt(0).toUpperCase()}
                                </div>
                            )}
                            <div>
                                <h2 className="text-2xl font-bold text-white">{stats.user.username}</h2>
                                <p className="text-purple-300">Level {stats.user.level} • {stats.user.xp} XP</p>
                            </div>
                            <div className="ml-auto text-right">
                                <div className="text-3xl font-bold text-white">{stats.tickets.completion_rate}%</div>
                                <div className="text-sm text-gray-300">Sprint Completion</div>
                            </div>
                        </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                            <div className="flex items-center gap-2 text-gray-400 mb-2">
                                <CheckCircle className="w-4 h-4" />
                                <span className="text-sm">Tickets Completed</span>
                            </div>
                            <div className="text-3xl font-bold text-green-400">{stats.tickets.completed}</div>
                            <div className="text-sm text-gray-500">of {stats.tickets.total} total</div>
                        </div>
                        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                            <div className="flex items-center gap-2 text-gray-400 mb-2">
                                <Target className="w-4 h-4" />
                                <span className="text-sm">Story Points</span>
                            </div>
                            <div className="text-3xl font-bold text-blue-400">{stats.story_points.completed}</div>
                            <div className="text-sm text-gray-500">of {stats.story_points.total} total</div>
                        </div>
                        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                            <div className="flex items-center gap-2 text-gray-400 mb-2">
                                <Clock className="w-4 h-4" />
                                <span className="text-sm">In Progress</span>
                            </div>
                            <div className="text-3xl font-bold text-yellow-400">{stats.tickets.in_progress}</div>
                            <div className="text-sm text-gray-500">tickets remaining</div>
                        </div>
                        <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                            <div className="flex items-center gap-2 text-gray-400 mb-2">
                                <Award className="w-4 h-4" />
                                <span className="text-sm">Standups</span>
                            </div>
                            <div className="text-3xl font-bold text-purple-400">{stats.standups_completed}</div>
                            <div className="text-sm text-gray-500">completed</div>
                        </div>
                    </div>

                    {/* Performance Metrics */}
                    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-purple-400" />
                            Performance Metrics
                        </h3>
                        <div className="grid grid-cols-5 gap-4">
                            {Object.entries(stats.metrics).map(([key, value]) => (
                                <div key={key} className="text-center">
                                    <div className={`text-2xl font-bold ${getMetricColor(value)}`}>{value}</div>
                                    <div className="text-xs text-gray-400 capitalize mt-1">{key}</div>
                                    <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                                        <div
                                            className={`h-2 rounded-full ${getMetricBg(value)} transition-all`}
                                            style={{ width: `${value}%` }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Continue Button */}
                    <div className="text-center">
                        <button
                            onClick={() => setStep('feedback')}
                            className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-8 rounded-full text-lg transition-transform hover:scale-105"
                        >
                            Continue to Feedback
                        </button>
                    </div>
                </div>
            )}

            {/* FEEDBACK STEP */}
            {step === 'feedback' && (
                <div className="space-y-8 max-w-2xl mx-auto animate-fade-in">
                    <div className="text-center mb-8">
                        <h1 className="text-3xl font-bold text-white">Sprint Feedback</h1>
                        <p className="text-gray-300 mt-2">Reflect on your sprint experience</p>
                    </div>

                    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                        <div className="flex items-center gap-2 mb-4">
                            <ThumbsUp className="w-5 h-5 text-green-400" />
                            <h3 className="text-lg font-semibold text-white">What went well?</h3>
                        </div>
                        <textarea
                            value={wentWell}
                            onChange={(e) => setWentWell(e.target.value)}
                            placeholder="Describe what worked well during this sprint..."
                            className="w-full h-32 bg-gray-900 border border-gray-600 rounded-lg p-4 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                        />
                    </div>

                    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
                        <div className="flex items-center gap-2 mb-4">
                            <ThumbsDown className="w-5 h-5 text-orange-400" />
                            <h3 className="text-lg font-semibold text-white">What could be improved?</h3>
                        </div>
                        <textarea
                            value={toImprove}
                            onChange={(e) => setToImprove(e.target.value)}
                            placeholder="Describe areas for improvement..."
                            className="w-full h-32 bg-gray-900 border border-gray-600 rounded-lg p-4 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                        />
                    </div>

                    <div className="flex justify-between">
                        <button
                            onClick={() => setStep('dashboard')}
                            className="text-gray-400 hover:text-white"
                        >
                            ← Back to Dashboard
                        </button>
                        <button
                            onClick={submitFeedback}
                            className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-full transition-transform hover:scale-105"
                        >
                            Complete Sprint ✓
                        </button>
                    </div>
                </div>
            )}

            {/* DONE STEP */}
            {step === 'done' && (
                <div className="space-y-8 animate-fade-in text-center max-w-2xl mx-auto">
                    <div className="w-24 h-24 bg-gradient-to-br from-green-400 to-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-2xl animate-bounce">
                        <PartyPopper className="w-12 h-12 text-white" />
                    </div>
                    <div>
                        <h1 className="text-5xl font-extrabold text-white mb-4">Sprint Complete!</h1>
                        <p className="text-2xl text-gray-300">Great job on completing your sprint.</p>
                    </div>
                    <div className="bg-gray-800/50 p-8 rounded-2xl border border-gray-700">
                        <p className="text-gray-300 leading-relaxed">
                            You've completed the sprint retrospective. Your feedback has been recorded.
                            Keep pushing code, stay reliable, and continue leveling up!
                        </p>
                    </div>
                    <button
                        onClick={() => navigate('/')}
                        className="text-blue-400 hover:text-white underline text-lg"
                    >
                        Return to Dashboard
                    </button>
                </div>
            )}
        </div>
    );
}
