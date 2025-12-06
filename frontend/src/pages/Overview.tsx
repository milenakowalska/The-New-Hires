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
    const [activities, setActivities] = useState<ActivityItem[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const userJson = localStorage.getItem('user');
                if (!userJson) return;
                const userData = JSON.parse(userJson);
                setUser(userData);

                const res = await api.get(`/gamification/me/stats?user_id=${userData.id}`);
                setStats(res.data);

                // Fetch recent activities
                const activityRes = await api.get(`/activity/recent?user_id=${userData.id}&limit=10`);
                setActivities(activityRes.data);
            } catch (error) {
                console.error("Failed to fetch stats", error);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();

        const onStatsUpdate = (data: Partial<UserStats>) => {
            setStats(prev => prev ? { ...prev, ...data } : data as UserStats);
        };

        const onLevelUp = (data: unknown) => {
            console.log("Level UP!", data);
        };

        const onNewActivity = (data: ActivityItem) => {
            // Add new activity to the top of the list
            setActivities(prev => [data, ...prev].slice(0, 10));
        };

        socket.on('stats_update', onStatsUpdate);
        socket.on('level_up', onLevelUp);
        socket.on('new_activity', onNewActivity);

        return () => {
            socket.off('stats_update', onStatsUpdate);
            socket.off('level_up', onLevelUp);
            socket.off('new_activity', onNewActivity);
        };
    }, []);

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

                {/* Recent Activity */}
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
                <div className="bg-white rounded-2xl p-4 shadow text-sm text-slate-500">
                    <div className="flex items-center gap-3">
                        <Calendar className="w-4 h-4" />
                        <div>
                            <div className="font-medium text-slate-900">Onboarding</div>
                            <div className="text-xs">Day 1 — Welcome & orientation</div>
                        </div>
                    </div>
                </div>
            </aside>
        </div>
    );
}
