'use client';
import { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  Users, 
  Package, 
  DollarSign, 
  ArrowUpRight, 
  ArrowDownRight,
  RefreshCcw,
  Loader2,
  Store
} from 'lucide-react';
import { 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { useShop } from '@/context/ShopContext';
import { apiUrl } from '@/lib/api';

export default function Dashboard() {
  const { selectedShopId, selectedShop, shops } = useShop();
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalOrders: 0,
    totalRevenue: 0,
    totalProfit: 0,
    totalCommission: 0,
    totalLogistic: 0,
    activeShops: 0
  });
  const [recentOrders, setRecentOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const productsParams = new URLSearchParams();
      const ordersParams = new URLSearchParams({ limit: '500' });
      if (selectedShopId) {
        productsParams.set('shop_id', String(selectedShopId));
        ordersParams.set('shop_id', String(selectedShopId));
      }

      const prodRes = await fetch(apiUrl(`/api/products/?${productsParams.toString()}`));
      const products = await prodRes.json();

      const orderRes = await fetch(apiUrl(`/api/orders/?${ordersParams.toString()}`));
      const orders = await orderRes.json();

      const revenue = Array.isArray(orders) ? orders.reduce((acc: number, o: any) => acc + (o.total_price || 0), 0) : 0;
      const profit = Array.isArray(orders) ? orders.reduce((acc: number, o: any) => acc + (o.seller_profit || 0), 0) : 0;
      const commission = Array.isArray(orders) ? orders.reduce((acc: number, o: any) => acc + (o.commission_amount || 0), 0) : 0;
      const logistic = Array.isArray(orders) ? orders.reduce((acc: number, o: any) => acc + (o.logistic_fee || 0), 0) : 0;

      setStats({
        totalProducts: Array.isArray(products) ? products.length : 0,
        totalOrders: Array.isArray(orders) ? orders.length : 0,
        totalRevenue: revenue,
        totalProfit: profit,
        totalCommission: commission,
        totalLogistic: logistic,
        activeShops: shops.length
      });
      setRecentOrders(Array.isArray(orders) ? orders.slice(0, 5) : []);
    } catch (error) {
      console.error('Xatolik:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedShopId]);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch(apiUrl('/api/sync/all'), { method: 'POST' });
      if (res.ok) {
        alert("Sinxronizatsiya boshlandi! Ma'lumotlar bir necha soniyadan so'ng yangilanadi.");
        setTimeout(fetchData, 5000);
      }
    } catch (error) {
      alert('Sinxronizatsiyada xatolik yuz berdi');
    } finally {
      setSyncing(false);
    }
  };

  const shopLabel = selectedShop ? selectedShop.name : "Barcha do'konlar";

  return (
    <div className="flex flex-col gap-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard</h1>
          <p className="text-[#94a3b8] mt-1 flex items-center gap-2">
            <Store size={14} className="text-[#7c3aed]" />
            {shopLabel}
            {selectedShop && <span className="text-xs bg-[#7c3aed]/10 text-[#7c3aed] px-2 py-0.5 rounded-full">ID: {selectedShop.uzum_shop_id}</span>}
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Jami Mahsulotlar" value={stats.totalProducts} icon={Package} color="#7c3aed" />
        <StatCard title="Jami Buyurtmalar" value={stats.totalOrders} icon={Users} color="#3b82f6" />
        <StatCard title="Umumiy Tushum" value={`${stats.totalRevenue.toLocaleString()} so'm`} icon={DollarSign} color="#10b981" />
        <StatCard title="Sof Foyda" value={`${stats.totalProfit.toLocaleString()} so'm`} icon={TrendingUp} color={stats.totalProfit >= 0 ? "#10b981" : "#ef4444"} />
      </div>

      {/* Qo'shimcha moliyaviy kartalar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-5 hover:border-[#f59e0b] transition-all">
          <p className="text-sm text-[#94a3b8] mb-1">Komissiya (Uzum)</p>
          <p className="text-xl font-bold text-[#f59e0b]">{stats.totalCommission.toLocaleString()} so'm</p>
        </div>
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-5 hover:border-[#ef4444] transition-all">
          <p className="text-sm text-[#94a3b8] mb-1">Logistika xarajati</p>
          <p className="text-xl font-bold text-[#ef4444]">{stats.totalLogistic.toLocaleString()} so'm</p>
        </div>
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-5 hover:border-[#3b82f6] transition-all">
          <p className="text-sm text-[#94a3b8] mb-1">Faol do'konlar</p>
          <p className="text-xl font-bold text-[#3b82f6]">{stats.activeShops} ta</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Orders */}
        <div className="lg:col-span-2 bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6 hover:border-[#7c3aed] transition-all">
          <h3 className="text-lg font-semibold text-white mb-6">Oxirgi buyurtmalar</h3>
          <div className="flex flex-col gap-4">
            {recentOrders.length > 0 ? recentOrders.map((order: any, i: number) => (
              <div key={i} className="flex items-center gap-4 group p-2 rounded-lg hover:bg-[#242830]/50 transition-all">
                <div className="w-10 h-10 bg-[#242830] rounded-xl flex items-center justify-center text-[#7c3aed] group-hover:bg-[#7c3aed] group-hover:text-white transition-all">
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

        {/* Do'konlar ro'yxati */}
        <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl p-6 hover:border-[#7c3aed] transition-all">
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
