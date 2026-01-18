import { useState, useEffect, useRef } from 'react';
import { MessageSquare, Send, X, Bot, Loader2, RefreshCw } from 'lucide-react';
import api from '../api/client';

export default function SeniorColleagueChat() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<{ role: 'user' | 'bot', text: string }[]>([
        { role: 'bot', text: "Hey there! I'm your senior colleague. I've looked through your repository—got any questions about how things work around here?" }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isSyncing, setIsSyncing] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
        setIsLoading(true);

        try {
            const userJson = localStorage.getItem('user');
            const userData = userJson ? JSON.parse(userJson) : { id: 1 };
            const res = await api.post(`/features/senior-colleague/chat?user_id=${userData.id}`, { message: userMsg });
            setMessages(prev => [...prev, { role: 'bot', text: res.data.response }]);
        } catch (error) {
            console.error("Chat failed:", error);
            setMessages(prev => [...prev, { role: 'bot', text: "Sorry, I'm having a bit of a brain fog right now. Can you try again?" }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSync = async () => {
        if (isSyncing) return;
        setIsSyncing(true);
        try {
            const userJson = localStorage.getItem('user');
            const userData = userJson ? JSON.parse(userJson) : { id: 1 };
            await api.post(`/features/senior-colleague/sync?user_id=${userData.id}`);
            setMessages(prev => [...prev, { role: 'bot', text: "Just finished re-reading your latest changes! I'm all up to date now." }]);
        } catch (error) {
            console.error("Sync failed:", error);
        } finally {
            setIsSyncing(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-50">
            {isOpen ? (
                <div className="bg-white w-96 h-[500px] rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300">
                    {/* Header */}
                    <div className="p-4 bg-slate-900 text-white flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                                <Bot className="w-5 h-5" />
                            </div>
                            <div>
                                <h4 className="font-semibold text-sm">Senior Colleague</h4>
                                <div className="flex items-center gap-1">
                                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
                                    <span className="text-[10px] text-slate-300 uppercase tracking-wider">Online</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleSync}
                                title="Sync with GitHub"
                                className={`p-1.5 hover:bg-slate-800 rounded-lg transition-colors ${isSyncing ? 'animate-spin' : ''}`}
                            >
                                <RefreshCw className="w-4 h-4 text-slate-400" />
                            </button>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors"
                            >
                                <X className="w-4 h-4 text-slate-400" />
                            </button>
                        </div>
                    </div>

                    {/* Chat Area */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${msg.role === 'user'
                                        ? 'bg-blue-600 text-white rounded-tr-none shadow-md'
                                        : 'bg-white text-slate-700 border border-slate-200 rounded-tl-none shadow-sm'
                                    }`}>
                                    {msg.text}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-white border border-slate-200 p-3 rounded-2xl rounded-tl-none shadow-sm">
                                    <Loader2 className="w-4 h-4 text-slate-400 animate-spin" />
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* Input */}
                    <form onSubmit={handleSend} className="p-4 bg-white border-t border-slate-100">
                        <div className="relative">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask about the codebase..."
                                className="w-full bg-slate-50 border-none rounded-xl py-3 pl-4 pr-12 text-sm focus:ring-2 focus:ring-blue-500/20 transition-all"
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-all shadow-sm"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                    </form>
                </div>
            ) : (
                <button
                    onClick={() => setIsOpen(true)}
                    className="w-14 h-14 bg-slate-900 text-white rounded-full flex items-center justify-center shadow-xl hover:bg-slate-800 hover:scale-110 transition-all duration-300 group"
                >
                    <div className="relative">
                        <MessageSquare className="w-6 h-6 group-hover:rotate-12 transition-transform" />
                        <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 border-2 border-slate-900 rounded-full"></span>
                    </div>
                </button>
            )}
        </div>
    );
}
