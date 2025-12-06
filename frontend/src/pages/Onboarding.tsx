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
    } | null>(null);

    useEffect(() => {
        // Fetch tasks
        const fetchTasks = async () => {
            const mockTasks = [
                { id: 1, task: "Clone the repository", completed: false, xp: 50 },
                { id: 2, task: "Open the project in your editor", completed: false, xp: 25 },
                { id: 3, task: "Open index.html in browser", completed: false, xp: 25 },
                { id: 4, task: "Find and fix your first bug", completed: false, xp: 100 },
                { id: 5, task: "Commit your fix", completed: false, xp: 50 },
            ];
            setTasks(mockTasks);
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
                project_description: projectDescription
            });

            setGeneratedResult({
                repo_url: res.data.repo_url,
                project_name: res.data.project_name,
                tickets_created: res.data.tickets_created
            });
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
        } catch (e: any) {
            console.error(e);
            const detail = e.response?.data?.detail || "Failed to generate repo";
            alert(detail);
        } finally {
            setLoading(false);
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
                <p className="text-gray-300 mb-6">
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
                    <div className="mt-6 bg-green-900/30 border border-green-500/30 rounded-lg p-4">
                        <h3 className="text-green-400 font-semibold mb-2">✓ Project Generated Successfully!</h3>
                        <div className="space-y-2 text-sm">
                            <p className="text-gray-300">
                                <span className="text-gray-500">Project:</span> {generatedResult.project_name}
                            </p>
                            <p className="text-gray-300">
                                <span className="text-gray-500">Tickets created:</span> {generatedResult.tickets_created}
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
                        <div key={task.id} className="p-4 border-b border-gray-800 flex items-center justify-between hover:bg-gray-800/50 transition-colors">
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
