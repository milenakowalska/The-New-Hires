import { Activity, CheckCircle, Calendar, Users, MessageCircle, GitBranch, Trophy, Code, ClipboardCheck } from 'lucide-react';
import { useEffect, useState } from 'react';
import api from '../api/client';
import socket from '../api/socket';

interface UserStats {
    level: number;
    xp: number;
    truthfulness: number;
    effort: number;
    reliability: number;
    collaboration: number;
    quality: number;
}

interface UserInfo {
    id: number;
    username: string;
    avatar_url: string;
    level: number;
    xp: number;
}

interface ActivityItem {
    id: number;
    type: string;
    description: string;
    extra_data: Record<string, unknown>;
    created_at: string;
}

// Format relative time (e.g., "2 mins ago")
const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
};

// Get icon based on activity type
const getActivityIcon = (type: string) => {
    switch (type) {
        case 'TICKET_ASSIGNED':
        case 'TICKET_COMPLETED':
            return <ClipboardCheck className="w-4 h-4 text-blue-600" />;
        case 'MESSAGE_SENT':
        case 'MESSAGE_RECEIVED':
            return <MessageCircle className="w-4 h-4 text-green-600" />;
        case 'REPO_CREATED':
            return <GitBranch className="w-4 h-4 text-purple-600" />;
        case 'STANDUP_COMPLETED':
            return <CheckCircle className="w-4 h-4 text-emerald-600" />;
        case 'CODE_REVIEW_SUBMITTED':
            return <Code className="w-4 h-4 text-orange-600" />;
        case 'ACHIEVEMENT_EARNED':
            return <Trophy className="w-4 h-4 text-yellow-600" />;
        default:
            return <Activity className="w-4 h-4 text-slate-600" />;
    }
};

export default function Overview() {
    const [stats, setStats] = useState<UserStats | null>(null);
    const [user, setUser] = useState<UserInfo | null>(null);
    const [sprintDay, setSprintDay] = useState(1);
    const [activities, setActivities] = useState<ActivityItem[]>([]);
    const [totalActivities, setTotalActivities] = useState(0);
    const [skip, setSkip] = useState(0);
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        try {
            const userJson = localStorage.getItem('user');
            if (!userJson) return;
            const userData = JSON.parse(userJson);
            setUser(userData);

            const [statsRes, activityRes, sprintRes] = await Promise.all([
                api.get(`/gamification/me/stats?user_id=${userData.id}`),
                api.get(`/activity/recent?user_id=${userData.id}&limit=5&skip=${skip}`),
                api.get(`/features/retrospectives/sprint-stats?user_id=${userData.id}`)
            ]);

            setStats(statsRes.data);
            setActivities(activityRes.data.items || []);
            setTotalActivities(activityRes.data.total || 0);
            setSprintDay(sprintRes.data.current_day || 1);
        } catch (error) {
            console.error("Failed to fetch stats", error);
        } finally {
            setLoading(false);
        }
    };

    const handleResetSprint = async () => {
        if (!user) return;
        try {
            await api.post(`/gamification/sprint/reset?user_id=${user.id}`);
            // Refetch everything
            fetchStats();
        } catch (error) {
            console.error("Failed to reset sprint", error);
        }
    };

    useEffect(() => {
        fetchStats();

        const onStatsUpdate = (data: Partial<UserStats>) => {
            setStats(prev => prev ? { ...prev, ...data } : data as UserStats);
        };

        const onLevelUp = (data: unknown) => {
            console.log("Level UP!", data);
        };

        const onNewActivity = (data: ActivityItem) => {
            // Add new activity to the top of the list if we are on the first page
            if (skip === 0) {
                setActivities(prev => [data, ...prev].slice(0, 5));
                setTotalActivities(prev => prev + 1);
            }
        };

        const onSprintUpdated = (data: { current_day: number }) => {
            setSprintDay(data.current_day);
        };

        socket.on('stats_update', onStatsUpdate);
        socket.on('level_up', onLevelUp);
        socket.on('new_activity', onNewActivity);
        socket.on('sprint_updated', onSprintUpdated);

        return () => {
            socket.off('stats_update', onStatsUpdate);
            socket.off('level_up', onLevelUp);
            socket.off('new_activity', onNewActivity);
            socket.off('sprint_updated', onSprintUpdated);
        };
    }, [skip]); // Refetch when skip changes

    if (loading) return <div className="text-center py-12">Loading...</div>;

    const metrics = [
        { key: 'Truthfulness', value: stats?.truthfulness ?? 0 },
        { key: 'Effort', value: stats?.effort ?? 0 },
        { key: 'Reliability', value: stats?.reliability ?? 0 },
        { key: 'Collaboration', value: stats?.collaboration ?? 0 },
        { key: 'Quality', value: stats?.quality ?? 0 },
    ];

    const squad = [
        { id: 'ai', name: 'AI', status: 'online' },
        { id: 'sarah', name: 'Sarah (AI)', status: 'online' },
        { id: 'jd', name: 'John Doe', status: 'offline' },
    ];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Main Content */}
            <section className="lg:col-span-2 space-y-6">
                {/* Player Card */}
                <div className="bg-white rounded-2xl p-6 shadow">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            {user?.avatar_url ? (
                                <img
                                    src={user.avatar_url}
                                    alt={user.username}
                                    className="w-16 h-16 rounded-full object-cover"
                                />
                            ) : (
                                <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-white text-xl font-bold">
                                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                                </div>
                            )}
                            <div>
                                <div className="flex items-baseline gap-3">
                                    <h2 className="text-lg font-semibold">{user?.username || 'User'}</h2>
                                    <span className="text-sm text-slate-500">Level {stats?.level} • {stats?.xp} XP</span>
                                </div>
                                <p className="text-sm text-slate-500">Welcome Back, {user?.username || 'User'}</p>
                            </div>
                        </div>

                        <div className="text-right max-w-md">
                            <p className="text-sm text-slate-500">Your performance metrics are being tracked in real-time.</p>
                            <p className="text-sm text-slate-400">Keep your stats high to survive the probationary period.</p>
                        </div>
                    </div>

                    {/* Metrics Grid */}
                    <div className="mt-6 grid grid-cols-2 md:grid-cols-5 gap-4">
                        {metrics.map((m) => (
                            <div key={m.key} className="p-3 bg-slate-50 rounded-lg text-center">
                                <div className="text-xs text-slate-500">{m.key}</div>
                                <div className="text-2xl font-semibold mt-1">{m.value}</div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Level Progress Bar */}
                <div className="bg-white rounded-2xl p-6 shadow flex items-center gap-6">
                    <div className="flex-1">
                        <h4 className="font-semibold">Level {stats?.level} / 100 XP</h4>
                        <div className="mt-3 w-full bg-slate-100 rounded-full h-3 overflow-hidden">
                            <div
                                className="h-3 rounded-full bg-indigo-500 transition-all"
                                style={{ width: `${(stats?.xp || 0) % 100}%` }}
                            />
                        </div>
                        <div className="text-xs text-slate-400 mt-2">{stats?.xp} XP</div>
                    </div>

                    <div className="w-48 text-center p-3 bg-slate-50 rounded-lg">
                        <div className="text-sm text-slate-500">Total XP</div>
                        <div className="text-2xl font-bold">{stats?.xp || 0}</div>
                    </div>
                </div>

                <div className="bg-white rounded-2xl p-6 shadow">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">Recent Activity</h3>
                        <div className="text-sm text-slate-500">Activity feed</div>
                    </div>

                    <ul className="divide-y">
                        {activities?.length === 0 ? (
                            <li className="py-6 text-center text-slate-400 text-sm">
                                No recent activity yet. Start completing tasks!
                            </li>
                        ) : (
                            activities?.map((activity) => (
                                <li key={activity.id} className="py-3 flex items-start gap-3">
                                    <div className="flex-none w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                                        {getActivityIcon(activity.type)}
                                    </div>
                                    <div className="flex-1">
                                        <div className="text-sm font-medium">{activity.description}</div>
                                        <div className="text-xs text-slate-400">{formatRelativeTime(activity.created_at)}</div>
                                    </div>
                                    <div className="flex-none text-xs text-slate-400">#{activity.type.toLowerCase().replace('_', '-')}</div>
                                </li>
                            ))
                        )}
                    </ul>

                    {/* Pagination Controls */}
                    {totalActivities > 5 && (
                        <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-50">
                            <button
                                onClick={() => setSkip(prev => Math.max(0, prev - 5))}
                                disabled={skip === 0}
                                className="text-xs px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-slate-600"
                            >
                                Previous
                            </button>
                            <div className="text-xs font-medium text-slate-500">
                                Page {Math.floor(skip / 5) + 1} of {Math.ceil(totalActivities / 5) || 1}
                            </div>
                            <button
                                onClick={() => setSkip(prev => prev + 5)}
                                disabled={skip + 5 >= totalActivities}
                                className="text-xs px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-slate-600"
                            >
                                Next
                            </button>
                        </div>
                    )}
                </div>
            </section>

            {/* Right Column - Sidebar */}
            <aside className="space-y-6">
                {/* Squad Status */}
                <div className="bg-white rounded-2xl p-4 shadow">
                    <div className="flex items-center justify-between mb-4">
                        <h4 className="font-semibold">Squad Status</h4>
                        <div className="text-xs text-slate-400">Realtime</div>
                    </div>

                    <ul className="space-y-3">
                        {squad.map((s) => (
                            <li key={s.id} className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                                    <Users className="w-4 h-4 text-slate-600" />
                                </div>
                                <div className="flex-1">
                                    <div className="text-sm font-medium">{s.name}</div>
                                    <div className="text-xs text-slate-400">{s.status}</div>
                                </div>
                                <div>
                                    {s.status === 'online' ? (
                                        <span className="inline-flex items-center gap-1 text-xs text-green-600">
                                            <CheckCircle className="w-3 h-3" /> Online
                                        </span>
                                    ) : (
                                        <span className="text-xs text-slate-400">Offline</span>
                                    )}
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Onboarding Info */}
                <div className="bg-white rounded-2xl p-4 shadow">
                    <div className="space-y-4">
                        <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${sprintDay >= 7 ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                                <Calendar className="w-5 h-5" />
                            </div>
                            <div>
                                <div className="font-semibold text-slate-900">Sprint Progress</div>
                                <div className="text-sm text-slate-500">Day {sprintDay} of 7</div>
                            </div>
                        </div>

                        {sprintDay >= 7 ? (
                            <div className="pt-2">
                                <div className="p-3 bg-green-50 rounded-xl border border-green-100 mb-3">
                                    <p className="text-xs text-green-700 font-medium">✨ Sprint Complete!</p>
                                    <p className="text-[10px] text-green-600 mt-1">You've survived the first week. Ready for the next one?</p>
                                </div>
                                <button
                                    onClick={handleResetSprint}
                                    className="w-full py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-semibold transition-colors shadow-sm"
                                >
                                    Start New Sprint
                                </button>
                            </div>
                        ) : (
                            <div className="pt-1">
                                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                                    <div
                                        className="bg-blue-500 h-full transition-all duration-500"
                                        style={{ width: `${(sprintDay / 7) * 100}%` }}
                                    />
                                </div>
                                <p className="text-[10px] text-slate-400 mt-2 text-center">Keep pushing to reach the sprint finish line!</p>
                            </div>
                        )}
                    </div>
                </div>
            </aside>
        </div>
    );
}
