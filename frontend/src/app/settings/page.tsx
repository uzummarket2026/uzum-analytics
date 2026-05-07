'use client';
import { useState, useEffect } from 'react';
import { Key, Save, CheckCircle, AlertTriangle, ShieldCheck, Info, Users, Loader2 } from 'lucide-react';
import { apiUrl, authFetch } from '@/lib/api';

interface UserItem {
  id: number;
  email: string;
  is_active: boolean;
}

export default function SettingsPage() {
  const [token, setToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  const [hasToken, setHasToken] = useState(false);

  // Foydalanuvchilarni boshqarish
  const [users, setUsers] = useState<UserItem[]>([]);
  const [me, setMe] = useState<UserItem | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editEmail, setEditEmail] = useState('');
  const [editPassword, setEditPassword] = useState('');
  const [savingUser, setSavingUser] = useState(false);
  const [userMsg, setUserMsg] = useState<{ type: 'success' | 'error', message: string } | null>(null);

  const fetchTokenStatus = async () => {
    try {
      const res = await authFetch(apiUrl('/api/settings/token'));
      const data = await res.json();
      setHasToken(data.has_token);
    } catch (error) {
      console.error('Xatolik:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const [usersRes, meRes] = await Promise.all([
        authFetch(apiUrl('/api/auth/users')),
        authFetch(apiUrl('/api/auth/me')),
      ]);
      if (usersRes.ok) setUsers(await usersRes.json());
      if (meRes.ok) setMe(await meRes.json());
    } catch (error) {
      console.error('Users yuklanmadi:', error);
    }
  };

  useEffect(() => {
    fetchTokenStatus();
    fetchUsers();
  }, []);

  const startEdit = (u: UserItem) => {
    setEditingId(u.id);
    setEditEmail(u.email);
    setEditPassword('');
    setUserMsg(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditEmail('');
    setEditPassword('');
  };

  const saveUser = async () => {
    if (editingId === null) return;
    setSavingUser(true);
    setUserMsg(null);
    try {
      const body: any = {};
      if (editEmail) body.email = editEmail;
      if (editPassword) body.password = editPassword;
      const res = await authFetch(apiUrl(`/api/auth/users/${editingId}`), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        setUserMsg({ type: 'success', message: 'Saqlandi' });
        cancelEdit();
        fetchUsers();
      } else {
        const err = await res.json().catch(() => ({}));
        setUserMsg({ type: 'error', message: err?.detail || 'Xato' });
      }
    } catch (e: any) {
      setUserMsg({ type: 'error', message: e?.message || 'Xato' });
    } finally {
      setSavingUser(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setStatus({ type: 'error', message: 'Iltimos, API tokeningizni kiriting.' });
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const res = await authFetch(apiUrl('/api/settings/'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'uzum_api_token', value: token })
      });
      if (res.ok) {
        setStatus({ type: 'success', message: 'API kalit muvaffaqiyatli saqlandi!' });
        setToken(''); // Clear input after save
        fetchTokenStatus();
      } else {
        setStatus({ type: 'error', message: 'Saqlashda xatolik yuz berdi.' });
      }
    } catch (error) {
      setStatus({ type: 'error', message: 'Server bilan bog\'lanib bo\'lmadi.' });
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto">
      <header>
        <h1 className="text-3xl font-bold text-white">Sozlamalar</h1>
        <p className="text-[#94a3b8] mt-1">Tizim sozlamalari va API kalitlarni boshqarish.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 space-y-6">
          <section className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6 hover:border-[#7c3aed] transition-all">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-[#7c3aed]/10 text-[#7c3aed] rounded-xl flex items-center justify-center">
                <Key size={20} />
              </div>
              <h2 className="text-xl font-semibold text-white">Uzum API Kaliti</h2>
            </div>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#94a3b8] mb-2">
                  API Token {hasToken && <span className="text-[#10b981] text-xs ml-2">(Saqlangan)</span>}
                </label>
                <input 
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder={hasToken ? "Yangi token kiriting..." : "rNLRZ0wGhitgYIaGTW1BOCUVTX..."}
                  className="w-full bg-[#0f1115] border border-[#2a2e37] rounded-xl py-3 px-4 text-white focus:outline-none focus:border-[#7c3aed] transition-all font-mono"
                />
                {hasToken && (
                  <p className="text-xs text-[#10b981] mt-2 flex items-center gap-1">
                    <CheckCircle size={12} />
                    Sizda API kalit saqlangan. Uni o'zgartirish uchun yangisini kiriting.
                  </p>
                )}
                {!hasToken && (
                  <p className="text-xs text-[#64748b] mt-2 flex items-center gap-1">
                    <ShieldCheck size={12} />
                    Kalitingiz shifrlangan holda bazada saqlanadi.
                  </p>
                )}
              </div>


              <button 
                type="submit"
                disabled={loading}
                className="flex items-center justify-center gap-2 w-full bg-[#7c3aed] hover:bg-[#6d28d9] disabled:bg-[#4c1d95] text-white py-3 rounded-xl font-semibold transition-all shadow-lg shadow-[#7c3aed]/20"
              >
                {loading ? <Save className="animate-spin" size={18} /> : <Save size={18} />}
                {loading ? 'Saqlanmoqda...' : 'Kalitni saqlash'}
              </button>
            </form>

            {status && (
              <div className={`mt-6 p-4 rounded-xl flex items-center gap-3 ${
                status.type === 'success' ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/20' : 'bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20'
              }`}>
                {status.type === 'success' ? <CheckCircle size={20} /> : <AlertTriangle size={20} />}
                <p className="text-sm font-medium">{status.message}</p>
              </div>
            )}
          </section>

          <section className="bg-[#1a1d23]/50 border border-[#2a2e37] border-dashed rounded-2xl p-6">
            <div className="flex items-start gap-4">
              <div className="w-8 h-8 bg-[#3b82f6]/10 text-[#3b82f6] rounded-lg flex items-center justify-center shrink-0">
                <Info size={18} />
              </div>
              <div>
                <h3 className="text-white font-medium">Kalitni qayerdan olish mumkin?</h3>
                <p className="text-sm text-[#94a3b8] mt-2 leading-relaxed">
                  Uzum Market Seller kabinetiga kiring.
                  <strong> "Sozlamalar" → "API" </strong> bo'limidan o'zingizning shaxsiy tokeningizni nusxalab oling va bu yerga joylashtiring.
                </p>
              </div>
            </div>
          </section>

          {/* Foydalanuvchilar boshqaruvi */}
          <section className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-[#7c3aed]/10 text-[#7c3aed] rounded-xl flex items-center justify-center">
                <Users size={20} />
              </div>
              <h2 className="text-xl font-semibold text-white">Foydalanuvchilar (Login/Parol)</h2>
            </div>

            {me && (
              <p className="text-xs text-[#94a3b8] mb-4">
                Hozirgi foydalanuvchi: <span className="text-[#a78bfa] font-mono">{me.email}</span>
              </p>
            )}

            <div className="space-y-3">
              {users.map(u => (
                <div key={u.id} className="bg-[#0f1115] border border-[#2a2e37] rounded-xl p-4">
                  {editingId === u.id ? (
                    <div className="space-y-3">
                      <label className="block text-xs text-[#94a3b8]">Login</label>
                      <input
                        type="text"
                        value={editEmail}
                        onChange={e => setEditEmail(e.target.value)}
                        className="w-full bg-[#1a1d23] border border-[#2a2e37] rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-[#7c3aed]"
                      />
                      <label className="block text-xs text-[#94a3b8]">Yangi parol (bo'sh qoldirsa o'zgarmaydi)</label>
                      <input
                        type="text"
                        value={editPassword}
                        onChange={e => setEditPassword(e.target.value)}
                        placeholder="Yangi parol..."
                        className="w-full bg-[#1a1d23] border border-[#2a2e37] rounded-lg px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-[#7c3aed]"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={saveUser}
                          disabled={savingUser}
                          className="flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] disabled:opacity-50 text-white px-4 py-1.5 rounded-lg text-sm transition-all"
                        >
                          {savingUser ? <Loader2 className="animate-spin" size={14} /> : <Save size={14} />}
                          Saqlash
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="bg-[#1a1d23] hover:bg-[#242830] border border-[#2a2e37] text-[#94a3b8] px-4 py-1.5 rounded-lg text-sm transition-all"
                        >
                          Bekor qilish
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium text-sm truncate">{u.email}</p>
                        <p className="text-[10px] text-[#64748b]">
                          ID: {u.id} {me?.id === u.id && "· (siz)"} {!u.is_active && "· faol emas"}
                        </p>
                      </div>
                      <button
                        onClick={() => startEdit(u)}
                        className="bg-[#0f1115] hover:bg-[#242830] border border-[#2a2e37] hover:border-[#7c3aed] text-[#94a3b8] hover:text-white px-3 py-1.5 rounded-lg text-xs transition-all"
                      >
                        Tahrirlash
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {userMsg && (
              <div className={`mt-4 p-3 rounded-xl flex items-center gap-2 text-sm ${
                userMsg.type === 'success' ? 'bg-[#10b981]/10 text-[#10b981] border border-[#10b981]/20' : 'bg-[#ef4444]/10 text-[#ef4444] border border-[#ef4444]/20'
              }`}>
                {userMsg.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                <span>{userMsg.message}</span>
              </div>
            )}
          </section>
        </div>

        <div className="space-y-6">
          <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6">
            <h3 className="text-white font-semibold mb-4">Xavfsizlik</h3>
            <ul className="space-y-4">
              <li className="flex gap-3 text-sm">
                <div className="w-1.5 h-1.5 bg-[#7c3aed] rounded-full mt-1.5 shrink-0" />
                <p className="text-[#94a3b8]">Tokenlar faqat sizning serveringizda saqlanadi.</p>
              </li>
              <li className="flex gap-3 text-sm">
                <div className="w-1.5 h-1.5 bg-[#7c3aed] rounded-full mt-1.5 shrink-0" />
                <p className="text-[#94a3b8]">Uzum API bilan barcha so'rovlar HTTPS orqali amalga oshiriladi.</p>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
