import React, { useState } from 'react';
import { Activity, Mail, Lock, ArrowRight, User, Hash, Calendar } from 'lucide-react';
import { extractErrorMessage } from '../services/errorUtils';

export default function LoginPage({ onLogin, onRegister }) {
  const [tab, setTab] = useState('login');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [regForm, setRegForm] = useState({
    name: '', email: '', password: '', confirmPassword: '', age: '', gender: 'M', grade_level: ''
  });

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await onLogin(loginForm.email, loginForm.password);
    } catch (err) {
      setError(extractErrorMessage(err, 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (regForm.password !== regForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (regForm.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(regForm.email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    try {
      await onRegister({
        name: regForm.name,
        email: regForm.email,
        password: regForm.password,
        age: parseInt(regForm.age),
        grade_level: parseInt(regForm.grade_level),
        gender: regForm.gender,
      });
    } catch (err) {
      setError(extractErrorMessage(err, 'Registration failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen app-wrapper flex items-center justify-center p-4 bg-gradient-to-br from-blue-900 via-blue-800 to-blue-950" style={{ width: '100%', position: 'absolute', top: 0, left: 0 }}>
      {/* Adding a global wrapper overrides the dark theme base applied by body from index.css for this page */}
      <div className="w-full max-w-md">
        {/* Header content */}
        <div className="animate-slide-left mb-8 text-center" style={{ animation: 'slideInLeft 0.6s ease-out' }}>
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="bg-blue-400 p-3 rounded-lg"><Activity size={32} color="white" /></div>
            <h1 className="text-3xl font-bold text-white mb-0 mt-0" style={{lineHeight: 1}}>PE System</h1>
          </div>
          <p className="text-blue-100 text-sm">Physical Education Management Platform</p>
        </div>
        
        {/* Auth Card */}
        <div className="animate-slide-right bg-white rounded-2xl shadow-2xl p-8" style={{ animation: 'slideInRight 0.6s ease-out' }}>
          
          <h2 className="text-2xl font-bold text-gray-800 mb-2 mt-0">
            {tab === 'login' ? 'Welcome Back' : 'Create Account'}
          </h2>
          <p className="text-gray-500 text-sm mb-8 mt-0">
            {tab === 'login' ? 'Sign in to your account to continue' : 'Enter your details to register'}
          </p>

          {error && <div className="mb-4 text-sm text-red-600 bg-red-100 border border-red-200 p-3 rounded-lg" style={{margin: 0, marginBottom: '16px'}}>{error}</div>}

          {tab === 'login' ? (
            <form onSubmit={handleLogin} className="space-y-4 m-0" style={{margin: 0}}>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 m-0">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 text-gray-400" size={20} />
                  <input type="email" required placeholder="your@email.com" 
                         className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900 transition-all focus:-translate-y-0.5"
                         value={loginForm.email} onChange={e => setLoginForm({...loginForm, email: e.target.value})} />
                </div>
              </div>
              <div className="space-y-2 mt-4">
                <div className="flex justify-between items-center m-0 mb-1">
                  <label className="block text-sm font-medium text-gray-700 m-0">Password</label>
                  <a href="#" className="text-xs text-blue-600 hover:text-blue-700 font-medium">Forgot?</a>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
                  <input type="password" required placeholder="••••••••" 
                         className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900 transition-all focus:-translate-y-0.5"
                         value={loginForm.password} onChange={e => setLoginForm({...loginForm, password: e.target.value})} />
                </div>
              </div>

              {/* Remember Me */}
              <div className="flex items-center gap-2 pt-2 mt-2">
                <input type="checkbox" id="remember" className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500" /> 
                <label htmlFor="remember" className="text-sm text-gray-600 m-0 cursor-pointer">Remember me</label>
              </div>

              <button type="submit" disabled={loading} 
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold py-2.5 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-300 transform hover:shadow-lg active:scale-95 mt-6 flex items-center justify-center gap-2 border-0 cursor-pointer">
                <span>{loading ? 'Signing in...' : 'Sign In'}</span>
                {!loading && <ArrowRight size={18} />}
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4 m-0" style={{margin: 0}}>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 m-0">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-3 text-gray-400" size={20} />
                  <input type="text" required placeholder="John Doe" 
                         className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900 transition-all focus:-translate-y-0.5"
                         value={regForm.name} onChange={e => setRegForm({...regForm, name: e.target.value})} />
                </div>
              </div>
              
              <div className="space-y-2 mt-4">
                <label className="block text-sm font-medium text-gray-700 m-0">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 text-gray-400" size={20} />
                  <input type="email" required placeholder="your@email.com" 
                         className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900 transition-all focus:-translate-y-0.5"
                         value={regForm.email} onChange={e => setRegForm({...regForm, email: e.target.value})} />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700 m-0">Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
                    <input type="password" required placeholder="••••••" minLength={6}
                           className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900 transition-all focus:-translate-y-0.5"
                           value={regForm.password} onChange={e => setRegForm({...regForm, password: e.target.value})} />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700 m-0">Confirm Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
                    <input type="password" required placeholder="••••••" minLength={6}
                           className={`w-full pl-10 pr-4 py-2.5 border rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900 transition-all focus:-translate-y-0.5 ${regForm.confirmPassword && regForm.password !== regForm.confirmPassword ? 'border-red-500' : 'border-gray-200'}`}
                           value={regForm.confirmPassword} onChange={e => setRegForm({...regForm, confirmPassword: e.target.value})} />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700 m-0">Age</label>
                  <div className="relative">
                    <Calendar className="absolute left-2 top-3 text-gray-400" size={16} />
                    <input type="number" required min={10} max={30} 
                           className="w-full pl-8 pr-2 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900"
                           value={regForm.age} onChange={e => setRegForm({...regForm, age: e.target.value})} />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700 m-0">Gender</label>
                  <select className="w-full px-3 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900"
                          value={regForm.gender} onChange={e => setRegForm({...regForm, gender: e.target.value})}>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700 m-0">Grade</label>
                  <div className="relative">
                    <Hash className="absolute left-2 top-3 text-gray-400" size={16} />
                    <input type="number" required min={1} max={12} 
                           className="w-full pl-8 pr-2 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 bg-white text-gray-900"
                           value={regForm.grade_level} onChange={e => setRegForm({...regForm, grade_level: e.target.value})} />
                  </div>
                </div>
              </div>

              <button type="submit" disabled={loading} 
                      className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-semibold py-2.5 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-300 transform hover:shadow-lg active:scale-95 mt-6 flex items-center justify-center gap-2 border-0 cursor-pointer">
                <span>{loading ? 'Registering...' : 'Create Account'}</span>
                {!loading && <ArrowRight size={18} />}
              </button>
            </form>
          )}

          <div className="flex items-center gap-3 my-6">
            <div className="flex-1 h-px bg-gray-200"></div>
            <span className="text-xs text-gray-400 m-0">OR</span>
            <div className="flex-1 h-px bg-gray-200"></div>
          </div>

          <p className="text-center text-sm text-gray-600 mb-0 m-0">
            {tab === 'login' ? (
              <>Don't have an account? <a href="#" onClick={(e) => { e.preventDefault(); setTab('register'); setError(''); }} className="text-blue-600 hover:text-blue-700 font-semibold cursor-pointer text-decoration-none">Create one</a></>
            ) : (
              <>Already have an account? <a href="#" onClick={(e) => { e.preventDefault(); setTab('login'); setError(''); }} className="text-blue-600 hover:text-blue-700 font-semibold cursor-pointer text-decoration-none">Sign in</a></>
            )}
          </p>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-blue-100 text-xs space-y-1">
         <p className="m-0 mb-1">© 2024 Physical Education System. All rights reserved.</p>
         <div className="flex gap-4 justify-center">
           <a href="#" className="hover:text-white transition">Privacy Policy</a>
           <a href="#" className="hover:text-white transition">Terms of Service</a>
         </div>
        </div>
      </div>
      
      {/* Keyframes style directly in component */}
      <style>{`
        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
