import { Github } from 'lucide-react';
import api from '../api/client';
import { useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

export default function Login() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const code = searchParams.get('code');

  const hasCalled = useRef(false);

  useEffect(() => {
    const handleCallback = async (authCode: string) => {
      try {
        const res = await api.get(`/auth/github/callback?code=${authCode}`);
        if (res.data.access_token) {
          localStorage.setItem('token', res.data.access_token);
          localStorage.setItem('user', JSON.stringify(res.data.user));
          navigate('/');
        }
      } catch (error) {
        console.error("Login failed", error);
      }
    };

    if (code) {
      hasCalled.current = true;
      handleCallback(code);
    }
  }, [code, navigate]);

  const handleLogin = async () => {
    try {
      const res = await api.get('/auth/github/login');
      if (res.data?.url) {
        window.location.href = res.data.url;
      } else {
        console.error("Invalid login response", res.data);
        alert("Server error: Could not get login URL");
      }
    } catch (error) {
      console.error("Failed to get auth URL", error);
      alert("Failed to connect to backend. Check console for details.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-slate-900 p-8 rounded-xl border border-slate-800 shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              The New Hire
            </h1>
            <p className="text-slate-400">Can you survive the first week?</p>
          </div>

          <button
            onClick={handleLogin}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center transition-colors"
          >
            <Github className="w-5 h-5 mr-2" />
            Continue with GitHub
          </button>

          <p className="text-xs text-slate-500 text-center mt-6">
            By joining, you agree to fix all bugs assigned to you.
          </p>
        </div>
      </div>
    </div>
  );
}
