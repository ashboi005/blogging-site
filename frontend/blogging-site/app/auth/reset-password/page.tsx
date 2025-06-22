'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { BackgroundPaths } from '@/components/auth/background-paths'

export default function ResetPasswordPage() {
  const router = useRouter()
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [refreshToken, setRefreshToken] = useState<string | null>(null)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(true)

  useEffect(() => {
    // Tokens are in the URL fragment, not query params
    const hash = window.location.hash.substring(1)
    const params = new URLSearchParams(hash)
    const accessTokenFromUrl = params.get('access_token')
    const refreshTokenFromUrl = params.get('refresh_token')
    const errorDescription = params.get('error_description')

    if (errorDescription) {
      setError(errorDescription.replace(/\+/g, ' '))
      setIsVerifying(false)
      return
    }

    if (accessTokenFromUrl && refreshTokenFromUrl) {
      setAccessToken(accessTokenFromUrl)
      setRefreshToken(refreshTokenFromUrl)
    } else {
      setError('Invalid or missing reset token information in URL.')
    }
    setIsVerifying(false)
  }, [])

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setMessage(null)

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (!accessToken || !refreshToken) {
      setError('No reset token found. Please use the link from your email.')
      return
    }

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/auth/reset-password`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            access_token: accessToken,
            refresh_token: refreshToken,
            new_password: password,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to reset password.')
      }

      setMessage(
        data.message ||
          'Password has been reset successfully. You can now log in with your new password.'
      )
      setTimeout(() => {
        router.push('/auth')
      }, 3000)
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="min-h-screen bg-black/93 text-white flex items-center justify-center p-4 relative overflow-hidden">
      <BackgroundPaths />
      <div className="relative z-10 max-w-sm w-full bg-white/10 backdrop-blur-md rounded-3xl p-8 border border-white/20 shadow-2xl shadow-blue-500/10">
        <h1 className="text-center font-bold text-3xl text-white">Reset Password</h1>

        {isVerifying && (
          <p className="text-center mt-4">Verifying reset link...</p>
        )}

        {error && (
          <p className="bg-red-500/50 text-white p-3 rounded-lg mt-4 text-center">
            {error}
          </p>
        )}
        
        {message && (
          <p className="bg-green-500/50 text-white p-3 rounded-lg mt-4 text-center">
            {message}
          </p>
        )}

        {!isVerifying && !error && !message && (
          <form onSubmit={handleResetPassword} className="mt-5">
            <input
              className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
              type="password"
              placeholder="New Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <input
              className="w-full bg-white/20 border-2 border-transparent py-4 px-5 rounded-2xl mt-4 focus:outline-none focus:border-cyan-400 text-white placeholder-gray-300"
              type="password"
              placeholder="Confirm New Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
            <button
              className="block w-full font-bold bg-gradient-to-r from-blue-600 to-cyan-500 text-white py-4 my-5 rounded-2xl shadow-xl shadow-blue-400/50 border-none transition hover:scale-105 active:scale-95"
              type="submit"
            >
              Reset Password
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
