import { Outlet, Link, useLocation } from 'react-router-dom';

import { useState, useEffect } from 'react';
import socket from '../api/socket';

export default function DashboardLayout() {
    const location = useLocation();
    const isActive = (path: string) => location.pathname === path;
    const [hasUnread, setHasUnread] = useState(false);

    useEffect(() => {
        const onNewMessage = (msg: any) => {
            // Only show dot if we are NOT on the messages page
            if (!location.pathname.startsWith('/messages')) {
                setHasUnread(true);
            }
        };

        socket.on('new_message', onNewMessage);

        return () => {
            socket.off('new_message', onNewMessage);
        };
    }, [location.pathname]);

    // Clear unread if we navigate to messages
    useEffect(() => {
        if (location.pathname.startsWith('/messages')) {
            setHasUnread(false);
        }
    }, [location.pathname]);

    const navItems = [
        { path: '/', label: 'Overview' },
        { path: '/onboarding', label: 'Onboarding' },
        { path: '/sprint', label: 'Sprint Board' },
        { path: '/standup', label: 'Standup Meeting' },
        { path: '/retrospective', label: 'Retrospective' },
        { path: '/messages', label: 'Messages' },
    ];

    const handleLogout = () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    };

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Top Header Navigation */}
            <header className="bg-white border-b border-slate-200">
                <div className="max-w-7xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between">
                        {/* Logo/Brand */}
                        <div>
                            <h1 className="text-2xl font-semibold text-slate-900">The New Hire</h1>
                            <p className="text-sm text-slate-500">
                                Day <span className="font-medium">1</span> of <span className="font-medium">7</span>
                            </p>
                        </div>

                        {/* Navigation Links */}
                        <nav className="flex items-center gap-6">
                            {navItems.map((item) => (
                                <Link
                                    key={item.path}
                                    to={item.path}
                                    className={`text-sm ${isActive(item.path)
                                        ? 'text-slate-900 font-medium'
                                        : 'text-slate-600 hover:text-slate-900'
                                        }`}
                                >
                                    {item.label}
                                    {item.label === 'Messages' && hasUnread && (
                                        <span className="ml-2 w-2 h-2 bg-red-500 rounded-full inline-block"></span>
                                    )}
                                </Link>
                            ))}

                            <button
                                onClick={handleLogout}
                                className="ml-4 px-4 py-1.5 text-sm bg-rose-500 text-white rounded hover:bg-rose-600 transition-colors"
                            >
                                Logout
                            </button>
                        </nav>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-6 py-6">
                <Outlet />
            </main>
        </div>
    );
}
