'use client';
import { useEffect, useState } from 'react';
import { RefreshCcw, Loader2, RotateCcw, AlertCircle } from 'lucide-react';
import { apiUrl } from '@/lib/api';

export default function ReturnsPage() {
  const [returns, setReturns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchReturns = async () => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl('/api/returns/'));
      const data = await res.json();
      if (Array.isArray(data)) {
        setReturns(data);
      }
    } catch (error) {
      console.error('Xatolik:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturns();
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Qaytarishlar</h1>
          <p className="text-[#94a3b8] mt-1">Xaridorlar tomonidan qaytarilgan mahsulotlar ro'yxati.</p>
        </div>
        <button 
          onClick={fetchReturns}
          className="flex items-center gap-2 bg-[#1a1d23] border border-[#2a2e37] hover:border-[#7c3aed] text-white px-4 py-2 rounded-xl transition-all"
        >
          <RefreshCcw size={18} />
          Yangilash
        </button>
      </header>

      <div className="bg-[#1a1d23] border border-[#2a2e37] rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-[#242830]/50">
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Return ID</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Sana</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Mahsulotlar</th>
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
              ) : returns.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-[#94a3b8]">
                    Qaytarilgan mahsulotlar topilmadi.
                  </td>
                </tr>
              ) : (
                returns.map((ret: any) => (
                  <tr key={ret.id} className="hover:bg-[#242830]/30 transition-all">
                    <td className="px-6 py-4">
                      <span className="text-white font-medium">#{ret.uzum_return_id}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#ef4444]/10 text-[#ef4444]`}>
                        <RotateCcw size={12} />
                        {ret.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-[#94a3b8]">
                      {new Date(ret.created_at).toLocaleDateString('uz-UZ')}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-2">
                        {ret.items?.map((item: any) => (
                          <div key={item.id} className="flex items-center gap-2 text-sm">
                            <AlertCircle size={14} className="text-[#f59e0b]" />
                            <span className="text-white">SKU: {item.sku_id}</span>
                            <span className="text-[#94a3b8]">({item.quantity} ta)</span>
                            <span className="text-xs italic text-[#94a3b8]">— {item.reason}</span>
                          </div>
                        ))}
                      </div>
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
