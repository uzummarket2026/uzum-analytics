'use client';
import { useEffect, useState } from 'react';
import { ShoppingBag, Search, Filter, MoreVertical, RefreshCcw, Loader2, Store } from 'lucide-react';
import { useShop } from '@/context/ShopContext';
import { apiUrl } from '@/lib/api';

export default function OrdersPage() {
  const { selectedShopId, selectedShop } = useShop();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState('');

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('limit', '500');
      if (selectedShopId) params.set('shop_id', String(selectedShopId));
      
      const res = await fetch(apiUrl(`/api/orders/?${params.toString()}`));
      const data = await res.json();
      if (Array.isArray(data)) {
        setOrders(data);
      } else {
        setOrders([]);
      }
    } catch (error) {
      console.error('Xatolik:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [selectedShopId]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      await fetch(apiUrl('/api/sync/all'), { method: 'POST' });
      setTimeout(fetchOrders, 3000);
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setSyncing(false);
    }
  };

  const filteredOrders = search
    ? orders.filter(o =>
        String(o.uzum_order_id).includes(search) ||
        (o.sku_code && o.sku_code.toLowerCase().includes(search.toLowerCase())) ||
        (o.sku_title && o.sku_title.toLowerCase().includes(search.toLowerCase()))
      )
    : orders;

  const shopLabel = selectedShop ? selectedShop.name : "Barcha do'konlar";

  return (
    <div className="flex flex-col gap-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Buyurtmalar</h1>
          <p className="text-[#94a3b8] mt-1 flex items-center gap-2">
            <Store size={14} className="text-[#7c3aed]" />
            {shopLabel} — {filteredOrders.length} ta buyurtma
          </p>
        </div>
        <div className="flex gap-4">
          <button 
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 bg-[#1a1d23] border border-[#2a2e37] hover:border-[#7c3aed] text-white px-4 py-2 rounded-xl transition-all"
          >
            {syncing ? <Loader2 className="animate-spin" size={18} /> : <RefreshCcw size={18} />}
            Yangilash
          </button>
        </div>
      </header>

      <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-[#2a2e37] flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94a3b8]" size={18} />
            <input 
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buyurtma ID, SKU yoki nomi bo'yicha qidirish..." 
              className="w-full bg-[#0f1115] border border-[#2a2e37] rounded-xl py-2 pl-10 pr-4 text-white focus:outline-none focus:border-[#7c3aed] transition-all"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[#242830]/50">
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Buyurtma ID</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">SKU</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Miqdor</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Umumiy narx</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Komissiya</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Foyda</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Sana</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2e37]">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-[#94a3b8]">
                    <Loader2 className="animate-spin mx-auto mb-2" size={24} />
                    Yuklanmoqda...
                  </td>
                </tr>
              ) : filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-[#94a3b8]">
                    Buyurtmalar topilmadi. Avval sinxronizatsiya qiling.
                  </td>
                </tr>
              ) : (
                filteredOrders.map((order: any) => {
                  const profit = order.seller_profit || 0;
                  return (
                    <tr key={order.id} className="hover:bg-[#242830]/30 transition-all group">
                      <td className="px-6 py-4">
                        <span className="text-white font-medium">#{order.uzum_order_id}</span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <code className="text-[#a78bfa] text-xs bg-[#a78bfa]/10 px-2 py-0.5 rounded w-fit mb-1">
                            {order.sku_code || 'KODSIZ'}
                          </code>
                          <span className="text-[10px] text-[#94a3b8] truncate max-w-[150px]" title={order.sku_title}>
                            {order.sku_title || 'Nomsiz SKU'}
                          </span>
                          {order.sku_char_value && (
                            <span className="text-[9px] text-[#64748b]">
                              {order.sku_char_title}: {order.sku_char_value}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          order.status === 'to_withdraw' ? 'bg-[#10b981]/10 text-[#10b981]' :
                          order.status === 'canceled' || order.status === 'partially_cancelled' ? 'bg-[#ef4444]/10 text-[#ef4444]' :
                          'bg-[#f59e0b]/10 text-[#f59e0b]'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-[#94a3b8]">{order.quantity} ta</td>
                      <td className="px-6 py-4 text-white font-semibold">
                        {order.total_price?.toLocaleString()} so'm
                      </td>
                      <td className="px-6 py-4 text-[#f59e0b]">
                        {(order.commission_amount || 0).toLocaleString()} so'm
                      </td>
                      <td className={`px-6 py-4 font-bold ${profit >= 0 ? 'text-[#10b981]' : 'text-[#ef4444]'}`}>
                        {profit.toLocaleString()} so'm
                      </td>
                      <td className="px-6 py-4 text-[#94a3b8]">
                        {order.order_date ? new Date(order.order_date).toLocaleDateString('uz-UZ') : '-'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
