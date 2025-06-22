'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { BackgroundPaths } from '@/components/auth/background-paths'

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [forgotPassword, setForgotPassword] = useState(false)
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed')
      }

      Cookies.set('access_token', data.access_token, { expires: 1, secure: true, sameSite: 'strict' })
      Cookies.set('refresh_token', data.refresh_token, { expires: 7, secure: true, sameSite: 'strict' })
      router.push('/')
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, username, first_name: firstName, last_name: lastName }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed')
      }

      setMessage(data.message || 'Registration successful. Please check your email to verify your account.')
      setIsLogin(true)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send password reset email.')
      }

      setMessage(data.message)
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="min-h-screen bg-black/93 text-white flex items-center justify-center p-4 relative overflow-hidden">
      <BackgroundPaths />
      <div className="relative z-10 max-w-sm w-full bg-white/10 backdrop-blur-md rounded-3xl p-8 border border-white/20 shadow-2xl shadow-blue-500/10">
        {forgotPassword ? (
          <>
            <h1 className="text-center font-bold text-3xl text-white">Forgot Password</h1>
            {error && <p className="bg-red-500/50 text-white p-3 rounded-lg mt-4 text-center">{error}</p>}
            {message && <p className="bg-green-500/50 text-white p-3 rounded-lg mt-4 text-center">{message}</p>}
            <form onSubmit={handleForgotPassword} className="mt-5">
              <input
                className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
                type="email"
                placeholder="Enter your e-mail"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <button
                className="block w-full font-bold bg-gradient-to-r from-blue-600 to-cyan-500 text-white py-4 my-5 rounded-2xl shadow-xl shadow-blue-400/50 border-none transition hover:scale-105 active:scale-95"
                type="submit"
              >
                Send Reset Link
              </button>
            </form>
            <p className="text-center text-gray-300">
              <button
                className="text-cyan-400 hover:text-cyan-300 font-bold bg-transparent border-none"
                onClick={() => {
                  setForgotPassword(false)
                  setError(null)
                  setMessage(null)
                }}
              >
                Back to Sign In
              </button>
            </p>
          </>
        ) : (
          <>
            <h1 className="text-center font-bold text-3xl text-white">{isLogin ? 'Sign In' : 'Create Account'}</h1>
            
            {error && <p className="bg-red-500/50 text-white p-3 rounded-lg mt-4 text-center">{error}</p>}
            {message && <p className="bg-green-500/50 text-white p-3 rounded-lg mt-4 text-center">{message}</p>}

            <form onSubmit={isLogin ? handleLogin : handleRegister} className="mt-5">
              {!isLogin && (
                <>
                  <input
                    className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                  />
                  <input
                    className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
                    type="text"
                    placeholder="First Name"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                  />
                  <input
                    className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
                    type="text"
                    placeholder="Last Name"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                  />
                </>
              )}
              <input
                className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
                type="email"
                placeholder="E-mail"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <input
                className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              {isLogin && (
                <button
                  type="button"
                  className="block mt-2.5 ml-2.5 text-xs text-cyan-400 no-underline cursor-pointer hover:text-cyan-300 bg-transparent border-none text-left p-0"
                  onClick={() => {
                    setForgotPassword(true)
                    setError(null)
                    setMessage(null)
                  }}
                >
                  Forgot Password?
                </button>
              )}
              <button
                className="block w-full font-bold bg-gradient-to-r from-blue-600 to-cyan-500 text-white py-4 my-5 rounded-2xl shadow-xl shadow-blue-400/50 border-none transition hover:scale-105 active:scale-95"
                type="submit"
              >
                {isLogin ? 'Sign In' : 'Sign Up'}
              </button>
            </form>
            <p className="text-center text-gray-300">
              {isLogin ? "Don't have an account?" : 'Already have an account?'}{' '}
              <button
                className="text-cyan-400 hover:text-cyan-300 font-bold bg-transparent border-none"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError(null);
                  setMessage(null);
                }}
              >
                {isLogin ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
