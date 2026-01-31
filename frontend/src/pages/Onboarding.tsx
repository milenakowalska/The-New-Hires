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
        invite_status?: string;
        github_username?: string;
    } | null>(null);
    const [backendStack, setBackendStack] = useState('Python Flask');
    const [frontendStack, setFrontendStack] = useState('React');
    const [githubUsername, setGithubUsername] = useState('');

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
                frontend_stack: frontendStack,
                github_username: githubUsername || null
            });

            setGeneratedResult({
                repo_url: res.data.repo_url,
                project_name: res.data.project_name,
                tickets_created: res.data.tickets_created,
                is_fallback: res.data.is_fallback,
                invite_status: res.data.invite_status,
                github_username: res.data.github_username
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
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 border border-gray-700 shadow-xl relative overflow-hidden">
                {/* Background Decoration */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>

                <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="p-3 bg-purple-900/30 rounded-lg border border-purple-500/30">
                            <Sparkles className="w-6 h-6 text-purple-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white">Generate Your Training Project</h2>
                            <p className="text-gray-400 text-sm">Create a realistic codebase with intentional bugs to fix.</p>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Project Description</label>
                            <textarea
                                value={projectDescription}
                                onChange={(e) => setProjectDescription(e.target.value)}
                                placeholder="Describe the app you want to build (e.g. 'A kanban board for managing tasks')..."
                                className="w-full h-32 bg-black/20 border border-gray-600 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all resize-none"
                            />
                            {/* Example suggestions */}
                            <div className="flex flex-wrap gap-2 mt-3">
                                <span className="text-xs text-gray-500 py-1">Try:</span>
                                {exampleProjects.slice(0, 3).map((example, i) => (
                                    <button
                                        key={i}
                                        onClick={() => setProjectDescription(example)}
                                        className="text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-gray-600 text-gray-300 px-3 py-1 rounded-full transition-all"
                                    >
                                        {example.split(' ').slice(0, 3).join(' ')}...
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">Backend Stack</label>
                                <div className="relative">
                                    <select
                                        value={backendStack}
                                        onChange={(e) => setBackendStack(e.target.value)}
                                        className="w-full appearance-none bg-black/20 border border-gray-600 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                    >
                                        <option>Java Spring</option>
                                        <option>Python Django</option>
                                        <option>Python Flask</option>
                                        <option>C# dotnet</option>
                                    </select>
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-300">
                                        ▼
                                    </div>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">Frontend Stack</label>
                                <div className="relative">
                                    <select
                                        value={frontendStack}
                                        onChange={(e) => setFrontendStack(e.target.value)}
                                        className="w-full appearance-none bg-black/20 border border-gray-600 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                                    >
                                        <option>React</option>
                                        <option>Angular</option>
                                        <option>Vue</option>
                                        <option>Python Django templates</option>
                                    </select>
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-gray-300">
                                        ▼
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* GitHub Username Input */}
                        <div className="bg-purple-900/10 p-5 rounded-xl border border-purple-500/20">
                            <label className="block text-sm font-medium text-purple-200 mb-2">
                                Enable Direct Contributions (Recommended)
                            </label>
                            <p className="text-xs text-gray-300 mb-3 leading-relaxed">
                                Enter your GitHub username to be automatically invited as a <strong>Collaborator</strong>.
                                This allows you to push code directly to the repository without needing to fork it.
                            </p>
                            <input
                                type="text"
                                value={githubUsername}
                                onChange={(e) => setGithubUsername(e.target.value)}
                                placeholder="e.g. github-username"
                                className="w-full bg-black/20 border border-gray-600 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all"
                            />
                        </div>

                        <button
                            onClick={generateRepo}
                            disabled={loading || !projectDescription.trim()}
                            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white px-6 py-4 rounded-xl font-bold text-lg shadow-lg shadow-purple-900/20 flex items-center justify-center gap-3 transition-all transform hover:scale-[1.01] active:scale-[0.99]"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    <span>Building your project...</span>
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-5 h-5" />
                                    <span>Generate Project</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Success Result */}
            {generatedResult && (
                <div className={`rounded-2xl p-6 border ${generatedResult.is_fallback
                    ? "bg-orange-900/20 border-orange-500/30"
                    : "bg-green-900/20 border-green-500/30"}`}>

                    <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-full ${generatedResult.is_fallback ? "bg-orange-900/50 text-orange-400" : "bg-green-900/50 text-green-400"}`}>
                            {generatedResult.is_fallback ? <div className="text-xl">⚠</div> : <CheckCircle className="w-6 h-6" />}
                        </div>
                        <div className="flex-1">
                            {generatedResult.is_fallback ? (
                                <h3 className="text-xl font-bold text-orange-400 mb-1">Standard Project Generated</h3>
                            ) : (
                                <h3 className="text-xl font-bold text-green-400 mb-1">Project Generated Successfully!</h3>
                            )}

                            <p className="text-gray-300 mb-4">
                                Your repository <strong>{generatedResult.project_name}</strong> is ready.
                                {generatedResult.tickets_created && ` We've also created ${generatedResult.tickets_created} tickets for you to work on.`}
                            </p>

                            {/* Invitation Logic Display */}
                            <div className="bg-black/30 rounded-lg p-4 border border-white/10 mb-4">
                                <h4 className="text-sm font-semibold text-white mb-2 uppercase tracking-wider">Next Steps</h4>
                                {generatedResult.invite_status === "success" ? (
                                    <div className="flex items-start gap-3">
                                        <div className="w-1 h-full min-h-[24px] bg-green-500 rounded-full"></div>
                                        <div>
                                            <p className="text-green-300 font-medium mb-1">Invitation Sent!</p>
                                            <p className="text-sm text-gray-200">
                                                Please <strong>check your email</strong> (associated with GitHub) and <strong>accept the invitation</strong>.
                                                Once accepted, you can clone the repo and push changes directly.
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex items-start gap-3">
                                        <div className="w-1 h-full min-h-[24px] bg-yellow-500 rounded-full"></div>
                                        <div>
                                            <p className="text-yellow-300 font-medium mb-1">Direct Access Not Enabled</p>
                                            <p className="text-sm text-gray-400">
                                                {generatedResult.invite_status === "skipped"
                                                    ? "You didn't provide a username, so we couldn't invite you."
                                                    : `We tried to invite you but it failed (Error: ${generatedResult.invite_status}).`
                                                }
                                                <br />
                                                <span className="text-white mt-1 block">To contribute: Please <strong>Fork</strong> the repository to your own account, or contact an admin for manual access.</span>
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>

                            <a
                                href={generatedResult.repo_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors border border-gray-600"
                            >
                                <span>View Repository</span>
                                <span className="text-gray-400">→</span>
                            </a>
                        </div>
                    </div>
                </div>
            )}

            <div>
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">Onboarding Checklist</h1>
                        <p className="text-gray-300 text-sm">Complete these tasks to get started.</p>
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
        </div >
    );
}
