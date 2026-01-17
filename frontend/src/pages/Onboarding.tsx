import { useEffect, useState } from 'react';
import api from '../api/client';
import { CheckCircle, Circle, Sparkles, Loader2 } from 'lucide-react';

interface Task {
    id: number;
    task: string;
    completed: boolean;
    xp: number;
}

export default function Onboarding() {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(false);
    const [projectDescription, setProjectDescription] = useState('');
    const [generatedResult, setGeneratedResult] = useState<{
        repo_url?: string;
        project_name?: string;
        tickets_created?: number;
        is_fallback?: boolean;
    } | null>(null);
    const [backendStack, setBackendStack] = useState('Python Flask');
    const [frontendStack, setFrontendStack] = useState('React');

    useEffect(() => {
        const fetchTasks = async () => {
            try {
                const userJson = localStorage.getItem('user');
                if (!userJson) return;
                const user = JSON.parse(userJson);

                const res = await api.get(`/onboarding/checklist?user_id=${user.id}`);
                setTasks(res.data);
            } catch (e) {
                console.error("Failed to fetch onboarding tasks:", e);
            }
        };
        fetchTasks();
    }, []);

    const generateRepo = async () => {
        if (!projectDescription.trim()) {
            alert("Please describe what kind of project you want to build!");
            return;
        }

        setLoading(true);
        setGeneratedResult(null);

        try {
            const userJson = localStorage.getItem('user');
            if (!userJson) {
                alert("Please log in first");
                return;
            }
            const user = JSON.parse(userJson);

            const res = await api.post(`/onboarding/generate-repo?user_id=${user.id}`, {
                project_description: projectDescription,
                backend_stack: backendStack,
                frontend_stack: frontendStack
            });

            setGeneratedResult({
                repo_url: res.data.repo_url,
                project_name: res.data.project_name,
                tickets_created: res.data.tickets_created,
                is_fallback: res.data.is_fallback
            });

            // Reset checklist tasks locally
            setTasks(prevTasks => prevTasks.map(t => ({ ...t, completed: false })));

            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (e: any) {
            console.error(e);
            const detail = e.response?.data?.detail || "Failed to generate repo";
            alert(detail);
        } finally {
            setLoading(false);
        }
    };

    const toggleTask = async (taskId: number, currentStatus: boolean) => {
        if (currentStatus) return; // Already completed

        try {
            const userJson = localStorage.getItem('user');
            if (!userJson) return;
            const user = JSON.parse(userJson);

            await api.post(`/onboarding/complete-task?user_id=${user.id}`, {
                task_id: taskId
            });

            // Update local state
            setTasks(prev => prev.map(t =>
                t.id === taskId ? { ...t, completed: true } : t
            ));
        } catch (e) {
            console.error("Failed to complete task:", e);
        }
    };

    const exampleProjects = [
        "A weather app that shows current weather for any city",
        "A simple blog with posts and comments",
        "A recipe finder that searches by ingredients",
        "A quiz game with multiple choice questions",
        "A personal portfolio website",
        "A notes app with categories and search"
    ];

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Project Generator Section */}
            <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 rounded-2xl p-8 border border-purple-500/30">
                <div className="flex items-center gap-3 mb-4">
                    <Sparkles className="w-6 h-6 text-purple-400" />
                    <h2 className="text-2xl font-bold text-white">Generate Your Training Project</h2>
                </div>
                <p className="text-white mb-6">
                    Describe the project you want to build. Our AI will generate a beginner-friendly codebase
                    with intentional bugs and missing features for you to fix!
                </p>

                <div className="space-y-4">
                    <textarea
                        value={projectDescription}
                        onChange={(e) => setProjectDescription(e.target.value)}
                        placeholder="Example: A todo app with categories, due dates, and dark mode"
                        className="w-full h-24 bg-gray-900 border border-gray-600 rounded-lg p-4 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 resize-none"
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Backend Stack</label>
                            <select
                                value={backendStack}
                                onChange={(e) => setBackendStack(e.target.value)}
                                className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
                            >
                                <option>Java Spring</option>
                                <option>Python Django</option>
                                <option>Python Flask</option>
                                <option>C# dotnet</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-white mb-2">Frontend Stack</label>
                            <select
                                value={frontendStack}
                                onChange={(e) => setFrontendStack(e.target.value)}
                                className="w-full bg-gray-900 border border-gray-600 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
                            >
                                <option>React</option>
                                <option>Angular</option>
                                <option>Vue</option>
                                <option>Python Django templates</option>
                            </select>
                        </div>
                    </div>

                    {/* Example suggestions */}
                    <div className="flex flex-wrap gap-2">
                        <span className="text-xs text-gray-400">Try:</span>
                        {exampleProjects.slice(0, 3).map((example, i) => (
                            <button
                                key={i}
                                onClick={() => setProjectDescription(example)}
                                className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1 rounded-full transition-colors"
                            >
                                {example.slice(0, 40)}...
                            </button>
                        ))}
                    </div>

                    <button
                        onClick={generateRepo}
                        disabled={loading || !projectDescription.trim()}
                        className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white px-6 py-4 rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Generating project with AI... (this may take a moment)</span>
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5" />
                                <span>Generate Project</span>
                            </>
                        )}
                    </button>
                </div>

                {/* Success Result */}
                {generatedResult && (
                    <div className={`mt-6 rounded-lg p-4 border ${generatedResult.is_fallback
                        ? "bg-orange-900/30 border-orange-500/30"
                        : "bg-green-900/30 border-green-500/30"}`}>

                        {generatedResult.is_fallback ? (
                            <h3 className="text-orange-400 font-semibold mb-2">⚠ Warning: Standard Skeleton Created</h3>
                        ) : (
                            <h3 className="text-green-400 font-semibold mb-2">✓ Project Generated Successfully!</h3>
                        )}

                        {generatedResult.is_fallback && (
                            <p className="text-orange-200 text-sm mb-4">
                                Due to high demand, a standard project skeleton was created instead of a custom AI-generated one.
                            </p>
                        )}
                        <div className="space-y-2 text-sm">
                            <p className="text-white">
                                <span className="text-white font-medium">Project:</span> {generatedResult.project_name}
                            </p>
                            <p className="text-white">
                                <span className="text-white font-medium">Tickets created:</span> {generatedResult.tickets_created}
                            </p>
                            <a
                                href={generatedResult.repo_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-block mt-2 text-blue-400 hover:text-blue-300 underline"
                            >
                                View Repository on GitHub →
                            </a>
                        </div>
                    </div>
                )}
            </div>

            {/* Onboarding Checklist */}
            <div>
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">Onboarding Checklist</h1>
                        <p className="text-gray-400 text-sm">Complete these tasks to get started.</p>
                    </div>
                </div>

                <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                    {tasks.map((task) => (
                        <div
                            key={task.id}
                            onClick={() => toggleTask(task.id, task.completed)}
                            className={`p-4 border-b border-gray-800 flex items-center justify-between hover:bg-gray-800/50 transition-colors cursor-pointer ${task.completed ? 'opacity-75' : ''}`}
                        >
                            <div className="flex items-center">
                                {task.completed ?
                                    <CheckCircle className="w-6 h-6 text-green-500 mr-4" /> :
                                    <Circle className="w-6 h-6 text-gray-500 mr-4" />
                                }
                                <span className={task.completed ? "text-gray-500 line-through" : "text-gray-200"}>
                                    {task.task}
                                </span>
                            </div>
                            <span className="text-xs bg-gray-800 text-blue-400 px-2 py-1 rounded">
                                {task.xp} XP
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
