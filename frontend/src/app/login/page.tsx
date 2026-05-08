"use client"

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { apiUrl, setToken, getToken } from '@/lib/api'
import { Loader2, LogIn } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    if (getToken()) router.replace('/')
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const body = new URLSearchParams()
      body.set('username', email)
      body.set('password', password)
      const res = await fetch(apiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data?.detail || `Login xato (${res.status})`)
      }
      const data = await res.json()
      if (!data.access_token) throw new Error('Token kelmadi')
      setToken(data.access_token)
      router.replace('/')
    } catch (err: any) {
      setError(err?.message || 'Xato')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1115] py-12 px-4">
      <div className="max-w-md w-full bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-8">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-[#7c3aed] rounded-xl flex items-center justify-center font-extrabold text-white text-xl mx-auto mb-3">
            U
          </div>
          <h2 className="text-2xl font-bold text-white">Uzum Analytics</h2>
          <p className="text-sm text-[#94a3b8] mt-1">Hisobingizga kiring</p>
        </div>

        <form className="space-y-4" onSubmit={handleLogin}>
          <input
            type="text"
            required
            placeholder="Login"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="username"
            className="w-full bg-[#0f1115] border border-[#2a2e37] rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-[#7c3aed]"
          />
          <input
            type="password"
            required
            placeholder="Parol"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-[#0f1115] border border-[#2a2e37] rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-[#7c3aed]"
          />

          {error && (
            <div className="text-sm text-[#ef4444] bg-[#ef4444]/10 border border-[#ef4444]/30 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl transition-all"
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : <LogIn size={18} />}
            Kirish
          </button>
        </form>

      </div>
    </div>
  )
}
