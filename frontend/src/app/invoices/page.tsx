'use client';
import React, { useEffect, useState, Fragment } from 'react';
import { FileText, Search, Filter, MoreVertical, RefreshCcw, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { apiUrl } from '@/lib/api';

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | string | null>(null);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const res = await fetch(apiUrl('/api/invoices/'));
      const data = await res.json();
      if (Array.isArray(data)) {
        setInvoices(data);
      }
    } catch (error) {
      console.error('Xatolik:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Yukxatlar</h1>
          <p className="text-[#94a3b8] mt-1">Ta'minot va mahsulot qabul qilish nakladnoylari.</p>
        </div>
        <button 
          onClick={fetchInvoices}
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
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider w-10"></th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Invoys ID</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Status</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Turi</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Sana</th>
                <th className="px-6 py-4 text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">Tovarlar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2e37]">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-[#94a3b8]">
                    <Loader2 className="animate-spin mx-auto mb-2" size={24} />
                    Yuklanmoqda...
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-[#94a3b8]">
                    Yukxatlar topilmadi.
                  </td>
                </tr>
              ) : (
                invoices.map((inv: any) => (
                  <Fragment key={inv.id}>
                    <tr 
                      className="hover:bg-[#242830]/30 transition-all cursor-pointer"
                      onClick={() => setExpandedId(expandedId === inv.id ? null : inv.id)}
                    >
                      <td className="px-6 py-4 text-[#94a3b8]">
                        {expandedId === inv.id ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-white font-medium">#{inv.uzum_invoice_id}</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#7c3aed]/10 text-[#7c3aed]`}>
                          {inv.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-[#94a3b8] capitalize">{inv.invoice_type}</td>
                      <td className="px-6 py-4 text-[#94a3b8]">
                        {new Date(inv.created_at).toLocaleDateString('uz-UZ')}
                      </td>
                      <td className="px-6 py-4 text-white font-semibold">
                        {inv.items?.length || 0} xil tovar
                      </td>
                    </tr>
                    {expandedId === inv.id && (
                      <tr className="bg-[#0f1115]">
                        <td colSpan={6} className="px-12 py-4">
                          <div className="grid grid-cols-3 gap-4">
                            {inv.items?.map((item: any) => (
                              <div key={item.id} className="bg-[#1a1d23] p-3 rounded-lg border border-[#2a2e37]">
                                <p className="text-xs text-[#94a3b8]">SKU ID: {item.sku_id}</p>
                                <p className="text-sm text-white font-bold mt-1">Miqdor: {item.quantity} ta</p>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
