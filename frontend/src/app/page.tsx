'use client';
import { useEffect, useState } from 'react';
import {
  TrendingUp,
  Users,
  Package,
  DollarSign,
  RefreshCcw,
  Loader2,
  Store,
  Calendar,
} from 'lucide-react';
import { useShop } from '@/context/ShopContext';
import { apiUrl, authFetch } from '@/lib/api';

type Preset = 'today' | 'current_month' | 'last_month' | 'current_year' | 'all' | 'custom';

function isoDate(d: Date) {
  // YYYY-MM-DD lokal sana
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function rangeFromPreset(preset: Preset): { from: string; to: string } | null {
  const now = new Date();
  if (preset === 'today') {
    return { from: isoDate(now), to: isoDate(now) };
  }
  if (preset === 'current_month') {
    const from = new Date(now.getFullYear(), now.getMonth(), 1);
    const to = new Date(now.getFullYear(), now.getMonth() + 1, 0); // joriy oy oxirgi kuni
    return { from: isoDate(from), to: isoDate(to) };
  }
  if (preset === 'last_month') {
    const from = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const to = new Date(now.getFullYear(), now.getMonth(), 0);
    return { from: isoDate(from), to: isoDate(to) };
  }
  if (preset === 'current_year') {
    const from = new Date(now.getFullYear(), 0, 1);
    return { from: isoDate(from), to: isoDate(now) };
  }
  return null; // all yoki custom
}

export default function Dashboard() {
  const { selectedShopIds, selectedShop, shops } = useShop();
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalOrders: 0,
    totalRevenue: 0,
    totalProfit: 0,
    totalToWithdraw: 0,
    totalCommission: 0,
    totalLogistic: 0,
    totalCost: 0,
    activeShops: 0,
    fboInventoryValue: 0,
  });
  const [recentOrders, setRecentOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  // Sana filtri
  const [preset, setPreset] = useState<Preset>('current_month');
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');

  const getRange = (): { from?: string; to?: string } => {
    if (preset === 'custom') {
      return { from: customFrom || undefined, to: customTo || undefined };
    }
    const r = rangeFromPreset(preset);
    return r ? { from: r.from, to: r.to } : {};
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const range = getRange();
      const productsParams = new URLSearchParams();
      const summaryParams = new URLSearchParams();
      const recentParams = new URLSearchParams({ limit: '5' });

      selectedShopIds.forEach(id => {
        const s = String(id);
        productsParams.append('shop_ids', s);
        summaryParams.append('shop_ids', s);
        recentParams.append('shop_ids', s);
      });
      if (range.from) {
        summaryParams.set('date_from', range.from);
        recentParams.set('date_from', range.from);
      }
      if (range.to) {
        summaryParams.set('date_to', range.to);
        recentParams.set('date_to', range.to);
      }

      const [prodSummaryRes, ordersSummaryRes, recentRes] = await Promise.all([
        authFetch(apiUrl(`/api/products/summary?${productsParams.toString()}`)),
        authFetch(apiUrl(`/api/orders/summary?${summaryParams.toString()}`)),
        authFetch(apiUrl(`/api/orders/?${recentParams.toString()}`)),
      ]);
      const prodSummary = await prodSummaryRes.json();
      const ordersSummary = await ordersSummaryRes.json();
      const recent = await recentRes.json();

      setStats({
        totalProducts: prodSummary.total_products || 0,
        totalOrders: ordersSummary.count || 0,
        totalRevenue: ordersSummary.revenue || 0,
        totalProfit: ordersSummary.profit || 0,
        totalToWithdraw: ordersSummary.to_withdraw || 0,
        totalCommission: ordersSummary.commission || 0,
        totalLogistic: ordersSummary.logistic || 0,
        totalCost: ordersSummary.purchase_total || 0,
        activeShops: shops.length,
        fboInventoryValue: prodSummary.total_fbo_value || 0,
      });
      setRecentOrders(Array.isArray(recent) ? recent : []);
    } catch (error) {
      console.error('Xatolik:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedShopIds, preset, customFrom, customTo]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await authFetch(apiUrl('/api/sync/all'), { method: 'POST' });
      if (res.ok) {
        setTimeout(fetchData, 5000);
      }
    } catch {
      alert('Sinxronizatsiyada xatolik');
    } finally {
      setSyncing(false);
    }
  };

  const shopLabel = selectedShopIds.length === 0
    ? "Barcha do'konlar"
    : selectedShopIds.length === 1
      ? (selectedShop?.name ?? `Do'kon #${selectedShopIds[0]}`)
      : `${selectedShopIds.length} ta do'kon`;
  const range = getRange();
  const periodLabel = (() => {
    if (preset === 'today') return 'Bugun';
    if (preset === 'current_month') return 'Joriy oy';
    if (preset === 'last_month') return "O'tgan oy";
    if (preset === 'current_year') return 'Joriy yil';
    if (preset === 'all') return 'Hammasi';
    return `${range.from || '—'} … ${range.to || '—'}`;
  })();

  return (
    <div className="flex flex-col gap-8">
      <header className="flex justify-between items-center flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-[#94a3b8] mt-1 flex items-center gap-2 flex-wrap">
            <Store size={14} className="text-[#7c3aed]" />
            {shopLabel}
            <span className="mx-1 text-[#475569]">·</span>
            <Calendar size={14} className="text-[#a78bfa]" />
            <span className="text-[#a78bfa]">{periodLabel}</span>
          </p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center gap-2 bg-[#7c3aed] hover:bg-[#6d28d9] disabled:bg-[#4c1d95] text-white px-6 py-3 rounded-xl font-semibold transition-all hover:scale-105 active:scale-95 shadow-lg shadow-[#7c3aed]/20"
        >
          {syncing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCcw size={18} />}
          {syncing ? 'Yangilanmoqda...' : "Ma'lumotlarni yangilash"}
        </button>
      </header>

      {/* Sana filtri */}
      <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-4 flex flex-wrap items-center gap-3">
        <span className="text-sm text-[#94a3b8] mr-2">Davr:</span>
        {([
          ['today', 'Bugun'],
          ['current_month', 'Joriy oy'],
          ['last_month', "O'tgan oy"],
          ['current_year', 'Joriy yil'],
          ['all', 'Hammasi'],
          ['custom', "Boshqa"],
        ] as [Preset, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setPreset(key)}
            className={`px-3 py-1.5 rounded-lg text-sm transition-all ${
              preset === key
                ? 'bg-[#7c3aed] text-white'
                : 'bg-[#0f1115] text-[#94a3b8] border border-[#2a2e37] hover:border-[#7c3aed]'
            }`}
          >
            {label}
          </button>
        ))}
        {preset === 'custom' && (
          <div className="flex items-center gap-2 ml-2">
            <input
              type="date"
              value={customFrom}
              onChange={(e) => setCustomFrom(e.target.value)}
              className="bg-[#0f1115] border border-[#2a2e37] rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-[#7c3aed]"
            />
            <span className="text-[#94a3b8]">—</span>
            <input
              type="date"
              value={customTo}
              onChange={(e) => setCustomTo(e.target.value)}
              className="bg-[#0f1115] border border-[#2a2e37] rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-[#7c3aed]"
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="FBO Ombor Qiymati" value={`${stats.fboInventoryValue.toLocaleString()} so'm`} icon={Package} color="#a855f7" />
        <StatCard title="Umumiy Tushum" value={`${stats.totalRevenue.toLocaleString()} so'm`} icon={DollarSign} color="#10b981" />
        <StatCard title="Sof Foyda" value={`${stats.totalProfit.toLocaleString()} so'm`} icon={TrendingUp} color={stats.totalProfit >= 0 ? '#10b981' : '#ef4444'} />
        <StatCard title="Buyurtmalar" value={stats.totalOrders.toLocaleString()} icon={Users} color="#3b82f6" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-5 hover:border-[#10b981] transition-all">
          <p className="text-sm text-[#94a3b8] mb-1">Chiqarishga</p>
          <p className="text-xl font-bold text-[#10b981]">{stats.totalToWithdraw.toLocaleString()} so'm</p>
        </div>
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-5 hover:border-[#f59e0b] transition-all">
          <p className="text-sm text-[#94a3b8] mb-1">Komissiya</p>
          <p className="text-xl font-bold text-[#f59e0b]">{stats.totalCommission.toLocaleString()} so'm</p>
        </div>
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-5 hover:border-[#ef4444] transition-all">
          <p className="text-sm text-[#94a3b8] mb-1">Logistika</p>
          <p className="text-xl font-bold text-[#ef4444]">{stats.totalLogistic.toLocaleString()} so'm</p>
        </div>
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-5 hover:border-[#94a3b8] transition-all">
          <p className="text-sm text-[#94a3b8] mb-1">Tannarx (jami)</p>
          <p className="text-xl font-bold text-[#94a3b8]">{stats.totalCost.toLocaleString()} so'm</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Oxirgi buyurtmalar</h3>
          <div className="flex flex-col gap-4">
            {loading ? (
              <div className="text-center py-10 text-[#94a3b8]">
                <Loader2 className="animate-spin mx-auto mb-2" size={20} />
                Yuklanmoqda...
              </div>
            ) : recentOrders.length > 0 ? recentOrders.map((order: any, i: number) => (
              <div key={i} className="flex items-center gap-4 group p-2 rounded-lg hover:bg-[#242830]/50 transition-all">
                <div className="w-10 h-10 bg-[#242830] rounded-xl flex items-center justify-center text-[#7c3aed]">
                  <Package size={20} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">
                    {order.sku_title || `#${order.uzum_order_id}`}
                  </p>
                  <p className="text-xs text-[#94a3b8]">
                    {order.sku_code && <span className="font-mono text-[#a78bfa]">SKU: {order.sku_code}</span>}
                    {' · '}{order.quantity} dona
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-white">{(order.total_price || 0).toLocaleString()} so'm</p>
                  {order.seller_profit != null && (
                    <p className={`text-xs font-medium ${order.seller_profit >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                      {order.seller_profit >= 0 ? '+' : ''}{order.seller_profit.toLocaleString()} foyda
                    </p>
                  )}
                </div>
              </div>
            )) : (
              <div className="text-center py-10 text-[#94a3b8]">
                <p className="text-sm">Buyurtmalar topilmadi</p>
              </div>
            )}
          </div>
        </div>

        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-6">Do'konlar</h3>
          <div className="flex flex-col gap-3">
            {shops.length > 0 ? shops.map((shop) => (
              <div key={shop.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-[#242830]/50 transition-all">
                <div className="w-8 h-8 bg-[#7c3aed]/10 rounded-lg flex items-center justify-center">
                  <Store size={14} className="text-[#7c3aed]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{shop.name}</p>
                  <p className="text-[10px] text-[#94a3b8]">{shop.product_count} mahsulot · {shop.order_count} buyurtma</p>
                </div>
              </div>
            )) : (
              <div className="text-center py-10 text-[#94a3b8]">
                <p className="text-sm">Sinxronizatsiya qiling</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color }: any) {
  return (
    <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6 hover:border-[color] transition-all group"
      style={{ '--hover-color': color } as any}
    >
      <div className="flex justify-between items-start mb-4">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center group-hover:scale-110 transition-all"
          style={{ backgroundColor: `${color}15`, color }}
        >
          <Icon size={24} />
        </div>
      </div>
      <div>
        <p className="text-sm text-[#94a3b8] font-medium">{title}</p>
        <p className="text-2xl font-bold text-white mt-1">{value}</p>
      </div>
    </div>
  );
}
