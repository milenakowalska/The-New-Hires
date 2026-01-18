import { useState, useEffect, useRef } from 'react';
import { useParams, NavLink } from 'react-router-dom';
import api from '../api/client';
import { Send, Hash, Users } from 'lucide-react';
import socket from '../api/socket';

interface Message {
    id: number;
    channel: string;
    content: string;
    sender_name: string;
    timestamp: string;
    is_bot: boolean;
    sender_avatar: string | null;
}

export default function Messages() {
    const { channel = 'general' } = useParams();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const isInitialLoad = useRef(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        isInitialLoad.current = true;
        const fetchMessages = async () => {
            try {
                const res = await api.get(`/messages/${channel}`);

                // If this is the general channel and there are no messages, add HR welcome
                if (channel === 'general' && res.data.length === 0) {
                    const userJson = localStorage.getItem('user');
                    if (userJson) {
                        const user = JSON.parse(userJson);
                        //  Create HR welcome message
                        await api.post('/messages', {
                            channel: 'general',
                            content: `Welcome to the team, ${user.username}! 🎉\n\nPlease start by completing your onboarding:\n1. Go to the Onboarding page\n2. Generate your repository\n3. Clone it locally\n4. Complete the setup checklist\n\nGood luck on your first week!`,
                            is_bot: true
                        });
                        // Refetch to get the welcome message
                        const refreshed = await api.get(`/messages/${channel}`);
                        setMessages(refreshed.data);
                        return;
                    }
                }

                setMessages(res.data);
            } catch (error) {
                console.log("Error fetching messages", error);
            }
        };

        // Fetch initial messages
        fetchMessages();


        // Socket Listener
        const onNewMessage = (msg: Message) => {
            if (msg.channel === channel) {
                setMessages(prev => [...prev, msg]);
            }
        };

        socket.on('new_message', onNewMessage);

        return () => {
            socket.off('new_message', onNewMessage);
        };
    }, [channel]);

    const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
        messagesEndRef.current?.scrollIntoView({ behavior });
    };

    useEffect(() => {
        if (messages.length > 0) {
            if (isInitialLoad.current) {
                scrollToBottom("auto");
                isInitialLoad.current = false;
            } else {
                scrollToBottom("smooth");
            }
        }
    }, [messages]);



    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        try {
            await api.post('/messages', {
                channel,
                content: input,
                is_bot: false
            });
            setInput('');
            // No need to fetch, socket will append
        } catch (error) {
            console.error("Failed to send", error);
        }
    };

    const channels = ['general', 'dev', 'code-review', 'random'];

    return (
        <div className="h-[calc(100vh-8rem)] flex bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
            {/* Channel List */}
            <div className="w-64 bg-gray-800/50 border-r border-gray-700 flex flex-col">
                <div className="p-4 border-b border-gray-700">
                    <h3 className="font-semibold text-white flex items-center">
                        <Users className="w-4 h-4 mr-2" />
                        Channels
                    </h3>
                </div>
                <div className="flex-1 p-2 space-y-1">
                    {channels.map(c => (
                        <NavLink
                            key={c}
                            to={`/messages/${c}`}
                            className={({ isActive }) => `flex items-center px-3 py-2 rounded-lg text-sm transition-colors ${isActive || (channel === c && window.location.pathname === '/messages') ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-700'}`}
                        >
                            <Hash className="w-4 h-4 mr-2 opacity-70" />
                            {c}
                        </NavLink>
                    ))}
                </div>
            </div>

            {/* Chat Area */}
            <div className="flex-1 flex flex-col">
                <div className="p-4 border-b border-gray-700 bg-gray-900 shadow-sm z-10">
                    <h3 className="font-bold text-white flex items-center">
                        <Hash className="w-5 h-5 mr-2 text-gray-500" />
                        {channel}
                    </h3>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg) => (
                        <div key={msg.id} className="flex items-start group">
                            {msg.sender_avatar ? (
                                <img src={msg.sender_avatar} alt={msg.sender_name} className="w-10 h-10 rounded-full object-cover mr-3 bg-gray-700" />
                            ) : (
                                <div className="w-10 h-10 rounded-full bg-gray-700 flex-shrink-0 mr-3 flex items-center justify-center text-sm font-bold text-gray-300">
                                    {msg.sender_name?.[0]?.toUpperCase() || '?'}
                                </div>
                            )}
                            <div className="flex-1">
                                <div className="flex items-baseline">
                                    <span className="font-medium text-white mr-2">{msg.sender_name}</span>
                                    <span className="text-xs text-gray-500">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                                <p className="text-gray-300 text-sm mt-0.5">{msg.content}</p>
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                <div className="p-4 bg-gray-800/50 border-t border-gray-800">
                    <form onSubmit={sendMessage} className="relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={`Message #${channel}`}
                            className="w-full bg-gray-900 border-none rounded-lg py-3 pl-4 pr-12 text-white placeholder-gray-500 focus:ring-1 focus:ring-blue-500"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim()}
                            className="absolute right-2 top-2 p-1.5 text-blue-500 hover:bg-blue-500/10 rounded-md transition-colors disabled:opacity-50"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
