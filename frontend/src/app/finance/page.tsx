'use client';
import { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  DollarSign, 
  ArrowUpRight, 
  ArrowDownRight,
  RefreshCcw,
  Loader2,
  PieChart as PieChartIcon,
  CreditCard,
  Wallet
} from 'lucide-react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar
} from 'recharts';
import { apiUrl, authFetch } from '@/lib/api';

export default function FinancePage() {
  const [stats, setStats] = useState({
    total_revenue: 0,
    total_expenses: 0,
    net_profit: 0,
    daily_stats: []
  });
  const [expenses, setExpenses] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const statsRes = await authFetch(apiUrl('/api/finance/stats'));
      const statsData = await statsRes.json();
      setStats(statsData);

      const expRes = await authFetch(apiUrl('/api/finance/expenses'));
      const expData = await expRes.json();
      setExpenses(expData);
    } catch (error) {
      console.error('Xatolik:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await authFetch(apiUrl('/api/finance/expenses/sync'), { method: 'POST' });
      setTimeout(fetchData, 3000);
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Moliya</h1>
          <p className="text-[#94a3b8] mt-1">Daromadlar, xarajatlar va foyda tahlili.</p>
        </div>
        <button 
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] disabled:bg-[#4c1d95] text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg shadow-[#7c3aed]/20"
        >
          {syncing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCcw size={18} />}
          Yangilash
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Umumiy Tushum" value={`${stats.total_revenue?.toLocaleString()} so'm`} icon={Wallet} trend="+12.5%" positive={true} />
        <StatCard title="Umumiy Xarajat" value={`${stats.total_expenses?.toLocaleString()} so'm`} icon={CreditCard} trend="-3.2%" positive={false} />
        <StatCard title="Sof Foyda" value={`${stats.net_profit?.toLocaleString()} so'm`} icon={TrendingUp} trend="+18.4%" positive={true} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6 hover:border-[#7c3aed] transition-all">
          <h3 className="text-lg font-semibold text-white mb-6">Savdolar Dinamikasi</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.daily_stats}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2e37" vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#1a1d23', border: '1px solid #2a2e37', borderRadius: '12px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="revenue" stroke="#7c3aed" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6 hover:border-[#7c3aed] transition-all">
          <h3 className="text-lg font-semibold text-white mb-6">Xarajatlar Tahlili</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={expenses.slice(0, 7)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2e37" vertical={false} />
                <XAxis dataKey="type" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#1a1d23', border: '1px solid #2a2e37', borderRadius: '12px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="amount" fill="#ef4444" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-[#2a2e37]">
          <h3 className="text-lg font-semibold text-white">Xarajatlar Ro'yxati</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[#242830]/50">
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Xarajat turi</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Miqdor</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Sana</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2e37]">
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-[#94a3b8]">
                    <Loader2 className="animate-spin mx-auto mb-2" size={24} />
                    Yuklanmoqda...
                  </td>
                </tr>
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-[#94a3b8]">
                    Xarajatlar topilmadi.
                  </td>
                </tr>
              ) : (
                expenses.map((exp: any) => (
                  <tr key={exp.id} className="hover:bg-[#242830]/30 transition-all">
                    <td className="px-6 py-4 text-white font-medium">{exp.type}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        exp.status === 'SUCCESS' ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-[#f59e0b]/10 text-[#f59e0b]'
                      }`}>
                        {exp.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-[#ef4444] font-semibold">
                      -{exp.amount?.toLocaleString()} so'm
                    </td>
                    <td className="px-6 py-4 text-[#94a3b8]">
                      {new Date(exp.created_at).toLocaleDateString('uz-UZ')}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend, positive }: any) {
  return (
    <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6 hover:border-[#7c3aed] transition-all group">
      <div className="flex justify-between items-start mb-4">
        <div className="w-12 h-12 bg-[#7c3aed]/10 text-[#7c3aed] rounded-xl flex items-center justify-center group-hover:bg-[#7c3aed] group-hover:text-white transition-all">
          <Icon size={24} />
        </div>
        <div className={`flex items-center gap-1 text-xs font-bold px-2 py-1 rounded-lg ${
          positive ? 'text-[#10b981] bg-[#10b981]/10' : 'text-[#ef4444] bg-[#ef4444]/10'
        }`}>
          {positive ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          {trend}
        </div>
      </div>
      <div>
        <p className="text-sm text-[#94a3b8] font-medium">{title}</p>
        <p className="text-2xl font-bold text-white mt-1">{value}</p>
      </div>
    </div>
  );
}
