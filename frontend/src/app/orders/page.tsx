'use client';
import { useEffect, useState } from 'react';
import { Search, RefreshCcw, Loader2, Store, ChevronLeft, ChevronRight, Calendar } from 'lucide-react';
import { useShop } from '@/context/ShopContext';
import { apiUrl, authFetch } from '@/lib/api';

const PAGE_SIZE = 100;

type Preset = 'today' | 'current_month' | 'last_month' | 'current_year' | 'all' | 'custom';

function isoDate(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function rangeFromPreset(preset: Preset): { from: string; to: string } | null {
  const now = new Date();
  if (preset === 'today') return { from: isoDate(now), to: isoDate(now) };
  if (preset === 'current_month') {
    const from = new Date(now.getFullYear(), now.getMonth(), 1);
    const to = new Date(now.getFullYear(), now.getMonth() + 1, 0);
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
  return null;
}

export default function OrdersPage() {
  const { selectedShopIds, selectedShop } = useShop();
  const [orders, setOrders] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<any>(null);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [preset, setPreset] = useState<Preset>('current_month');

  const dateRange = rangeFromPreset(preset);

  const buildParams = (extra: Record<string, string> = {}) => {
    const p = new URLSearchParams();
    selectedShopIds.forEach(id => p.append('shop_ids', String(id)));
    if (search) p.set('search', search);
    if (dateRange?.from) p.set('date_from', dateRange.from);
    if (dateRange?.to) p.set('date_to', dateRange.to);
    Object.entries(extra).forEach(([k, v]) => p.set(k, v));
    return p;
  };

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    const ctrl = new AbortController();
    const timeoutId = setTimeout(() => ctrl.abort(), 15000); // 15s timeout
    try {
      const listParams = buildParams({ limit: String(PAGE_SIZE), skip: String(page * PAGE_SIZE) });
      const summaryParams = buildParams();
      const [listRes, summaryRes] = await Promise.all([
        authFetch(apiUrl(`/api/orders/?${listParams.toString()}`), { signal: ctrl.signal }),
        authFetch(apiUrl(`/api/orders/summary?${summaryParams.toString()}`), { signal: ctrl.signal }),
      ]);
      if (!listRes.ok) throw new Error(`Orders ${listRes.status}`);
      if (!summaryRes.ok) throw new Error(`Summary ${summaryRes.status}`);
      const listData = await listRes.json();
      const summaryData = await summaryRes.json();
      setOrders(Array.isArray(listData) ? listData : []);
      setSummary(summaryData);
      setTotal(typeof summaryData?.count === 'number' ? summaryData.count : 0);
    } catch (e: any) {
      console.error('Orders fetch error:', e);
      setOrders([]);
      setTotal(0);
      if (e?.name === 'AbortError') {
        setError('Backend javob bermayapti (timeout). Server ishga tushirilganmi?');
      } else {
        setError(e?.message || 'Noma\'lum xato');
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedShopIds, page, search, preset]);

  useEffect(() => { setPage(0); }, [selectedShopIds, search, preset]);

  const [syncStatus, setSyncStatus] = useState<string>('');

  const handleSync = async () => {
    setSyncing(true);
    setSyncStatus('Boshlanyapti...');
    try {
      // 1. Qotib qolgan flagni reset qilish (xavfsiz)
      await authFetch(apiUrl('/api/sync/reset'), { method: 'POST' }).catch(() => {});

      // 2. Faqat buyurtma sync (tezroq)
      const startRes = await authFetch(apiUrl('/api/sync/orders'), { method: 'POST' });
      const startData = await startRes.json();
      console.log('Sync start:', startData);

      // 3. Tugaganini polling bilan kutish (max 3 daqiqa)
      const MAX_WAIT = 180_000;
      const POLL = 2_000;
      const t0 = Date.now();
      let lastResult: string | null = null;
      while (Date.now() - t0 < MAX_WAIT) {
        await new Promise(r => setTimeout(r, POLL));
        const sRes = await authFetch(apiUrl('/api/sync/status'));
        const s = await sRes.json();
        if (!s.running) {
          lastResult = s.last_error
            ? `Xato: ${s.last_error}`
            : `Tayyor: ${s.last_result || 'OK'}`;
          break;
        }
        setSyncStatus(`Sinxronlanmoqda... (${s.elapsed_sec}s)`);
      }
      setSyncStatus(lastResult || 'Vaqt tugadi (3 daq)');

      // 4. Buyurtmalarni qayta yuklash
      await fetchOrders();
    } catch (error: any) {
      console.error('Sync error:', error);
      setSyncStatus(`Xato: ${error?.message || 'noma\'lum'}`);
    } finally {
      setSyncing(false);
      setTimeout(() => setSyncStatus(''), 5000);
    }
  };

  const onSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput.trim());
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const shopLabel = selectedShopIds.length === 0
    ? "Barcha do'konlar"
    : selectedShopIds.length === 1
      ? (selectedShop?.name ?? `Do'kon #${selectedShopIds[0]}`)
      : `${selectedShopIds.length} ta do'kon`;
  const fromIdx = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const toIdx = Math.min((page + 1) * PAGE_SIZE, total);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Buyurtmalar</h1>
          <p className="text-[#94a3b8] mt-1 flex items-center gap-2">
            <Store size={14} className="text-[#7c3aed]" />
            {shopLabel} — jami {total.toLocaleString()} ta buyurtma
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 bg-[#1a1d23] border border-[#2a2e37] hover:border-[#7c3aed] disabled:opacity-50 text-white px-4 py-2 rounded-xl transition-all"
          >
            {syncing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCcw size={18} />}
            {syncing ? 'Sinxronlanmoqda...' : 'Yangilash'}
          </button>
          {syncStatus && (
            <span className="text-xs text-[#94a3b8] max-w-[300px] text-right">{syncStatus}</span>
          )}
        </div>
      </header>

      {/* Sana filtri */}
      <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-4 flex flex-wrap items-center gap-3">
        <Calendar size={14} className="text-[#a78bfa]" />
        <span className="text-sm text-[#94a3b8] mr-2">Davr:</span>
        {([
          ['today', 'Bugun'],
          ['current_month', 'Joriy oy'],
          ['last_month', "O'tgan oy"],
          ['current_year', 'Joriy yil'],
          ['all', 'Hammasi'],
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
      </div>

      {/* Summary kartochkalar */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-xl p-3">
            <p className="text-xs text-[#94a3b8]">Tushum</p>
            <p className="text-lg font-bold text-white">{(summary.revenue || 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-xl p-3">
            <p className="text-xs text-[#94a3b8]">Chiqarishga</p>
            <p className="text-lg font-bold text-[#10b981]">{(summary.to_withdraw || 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-xl p-3">
            <p className="text-xs text-[#94a3b8]">Tannarx</p>
            <p className="text-lg font-bold text-[#94a3b8]">{(summary.purchase_total || 0).toLocaleString()}</p>
          </div>
          <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-xl p-3">
            <p className="text-xs text-[#94a3b8]">Sof foyda</p>
            <p className={`text-lg font-bold ${(summary.profit || 0) >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
              {(summary.profit || 0).toLocaleString()}
            </p>
          </div>
        </div>
      )}

      <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-[#2a2e37] flex gap-4">
          <form onSubmit={onSearchSubmit} className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94a3b8]" size={18} />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Buyurtma ID, SKU yoki nomi bo'yicha qidirish... (Enter)"
              className="w-full bg-[#0f1115] border border-[#2a2e37] rounded-xl py-2 pl-10 pr-4 text-white focus:outline-none focus:border-[#7c3aed] transition-all"
            />
          </form>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[#242830]/50">
                <th className="px-3 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Status</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Sana</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">№ buyurtma</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">SKU / Nomi</th>
                <th className="px-3 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider text-center">Soni</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider text-right">Narx</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider text-right">Tannarx</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider text-right">Chiqarishga</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider text-right">Komissiya</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider text-right">Logistika</th>
                <th className="px-4 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider text-right">Foyda</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2e37]">
              {loading ? (
                <tr>
                  <td colSpan={11} className="px-6 py-12 text-center text-[#94a3b8]">
                    <Loader2 className="animate-spin mx-auto mb-2" size={24} />
                    Yuklanmoqda...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={11} className="px-6 py-12 text-center text-[#ef4444]">
                    {error}
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-6 py-12 text-center text-[#94a3b8]">
                    Buyurtmalar topilmadi.
                  </td>
                </tr>
              ) : (
                orders.map((order: any) => {
                  const cancelled = order.status === 'canceled' || order.status === 'partially_cancelled';
                  const isWithdraw = order.status === 'to_withdraw';
                  const dateStr = order.order_date
                    ? new Date(order.order_date).toLocaleDateString('uz-UZ')
                    : '-';
                  const timeStr = order.order_date
                    ? new Date(order.order_date).toLocaleTimeString('uz-UZ', { hour: '2-digit', minute: '2-digit' })
                    : '';
                  return (
                    <tr key={order.id} className="hover:bg-[#242830]/30 transition-all">
                      {/* Status icon */}
                      <td className="px-3 py-4">
                        <div className={`w-7 h-7 rounded-full flex items-center justify-center ${
                          isWithdraw ? 'bg-[#10b981]/15 text-[#10b981]' :
                          cancelled ? 'bg-[#ef4444]/15 text-[#ef4444]' :
                          'bg-[#f59e0b]/15 text-[#f59e0b]'
                        }`} title={order.status}>
                          {cancelled ? '✕' : isWithdraw ? '✓' : '⏱'}
                        </div>
                      </td>
                      {/* Sana */}
                      <td className="px-4 py-4">
                        <div className="flex flex-col">
                          <span className="text-white text-sm">{dateStr}</span>
                          <span className="text-[10px] text-[#64748b]">{timeStr}</span>
                        </div>
                      </td>
                      {/* № buyurtma */}
                      <td className="px-4 py-4">
                        <span className="text-white font-medium">
                          №{order.main_order_id ?? order.uzum_order_id}
                        </span>
                      </td>
                      {/* SKU / Nomi */}
                      <td className="px-4 py-4">
                        <div className="flex items-start gap-3">
                          {order.image_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img
                              src={order.image_url}
                              alt={order.sku_title || ''}
                              className="w-10 h-10 rounded-lg object-cover bg-[#0f1115] border border-[#2a2e37] flex-shrink-0"
                              onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
                            />
                          ) : (
                            <div className="w-10 h-10 rounded-lg bg-[#0f1115] border border-[#2a2e37] flex-shrink-0" />
                          )}
                          <div className="flex flex-col min-w-0">
                            <code className="text-[#a78bfa] text-xs bg-[#a78bfa]/10 px-1.5 py-0.5 rounded w-fit mb-0.5">
                              {order.sku_code || 'KODSIZ'}
                            </code>
                            <span className="text-[11px] text-[#94a3b8] truncate max-w-[200px]" title={order.sku_title}>
                              {order.sku_title || 'Nomsiz SKU'}
                            </span>
                          </div>
                        </div>
                      </td>
                      {/* Soni */}
                      <td className="px-3 py-4 text-center text-[#94a3b8]">{order.quantity}</td>
                      {/* Narx */}
                      <td className="px-4 py-4 text-right text-white">
                        {(order.total_price || 0).toLocaleString()}
                      </td>
                      {/* Tannarx */}
                      <td className="px-4 py-4 text-right text-[#94a3b8]">
                        {(order.purchase_total || 0).toLocaleString()}
                      </td>
                      {/* K vivodu */}
                      <td className={`px-4 py-4 text-right font-semibold ${
                        cancelled ? 'text-[#64748b]' : 'text-[#10b981]'
                      }`}>
                        {(order.to_withdraw_amount || 0).toLocaleString()}
                      </td>
                      {/* Komissiya */}
                      <td className="px-4 py-4 text-right text-[#f59e0b]">
                        {(order.commission_amount || 0).toLocaleString()}
                      </td>
                      {/* Logistika */}
                      <td className="px-4 py-4 text-right text-[#94a3b8]">
                        {(order.logistic_fee || 0).toLocaleString()}
                      </td>
                      {/* Foyda = Chiqarishga − Tannarx */}
                      {(() => {
                        const foyda = (order.to_withdraw_amount || 0) - (order.purchase_total || 0);
                        return (
                          <td className={`px-4 py-4 text-right font-bold ${
                            cancelled ? 'text-[#64748b]' :
                            foyda >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'
                          }`}>
                            {foyda.toLocaleString()}
                          </td>
                        );
                      })()}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {total > 0 && (
          <div className="flex justify-between items-center px-6 py-4 border-t border-[#2a2e37]">
            <span className="text-sm text-[#94a3b8]">
              {fromIdx.toLocaleString()}–{toIdx.toLocaleString()} / {total.toLocaleString()}
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0 || loading}
                className="flex items-center gap-1 bg-[#0f1115] border border-[#2a2e37] hover:border-[#7c3aed] disabled:opacity-40 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-lg transition-all"
              >
                <ChevronLeft size={16} /> Oldingi
              </button>
              <span className="text-sm text-[#94a3b8] px-3">
                Sahifa {page + 1} / {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1 || loading}
                className="flex items-center gap-1 bg-[#0f1115] border border-[#2a2e37] hover:border-[#7c3aed] disabled:opacity-40 disabled:cursor-not-allowed text-white px-3 py-1.5 rounded-lg transition-all"
              >
                Keyingi <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
