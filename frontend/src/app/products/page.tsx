'use client';
import React, { useEffect, useState, useMemo } from 'react';
import { Package, Search, RefreshCcw, ChevronRight, ChevronDown, Loader2, Store, TrendingDown, TrendingUp } from 'lucide-react';
import { useShop } from '@/context/ShopContext';
import { apiUrl, API_BASE_URL } from '@/lib/api';

export default function ProductsPage() {
  const { shops, selectedShopId, selectedShop } = useShop();
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [stockFilter, setStockFilter] = useState<'all' | 'instock' | 'out'>('all');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const itemsPerPage = 30;

  useEffect(() => { fetchData(); }, [selectedShopId]);

  async function fetchData() {
    setLoading(true);
    try {
      const params = selectedShopId ? `?shop_id=${selectedShopId}` : '';
      const res = await fetch(apiUrl(`/api/products/${params}`));
      const data = await res.json();
      if (Array.isArray(data)) setProducts(data);
    } catch (error) {
      console.error(`Ma'lumot yuklashda xato:`, error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSync() {
    setLoading(true);
    try {
      await fetch(apiUrl('/api/sync/all'), { method: 'POST' });
      await new Promise(r => setTimeout(r, 3000));
      await fetchData();
    } catch (error) {
      console.error('Sinxronizatsiya xatosi:', error);
    } finally {
      setLoading(false);
    }
  }

  // Guruhlar: uzum_product_id bo'yicha
  const filteredGroups = useMemo(() => {
    const groups: Record<number, any[]> = {};
    products.forEach(p => {
      if (!groups[p.uzum_product_id]) groups[p.uzum_product_id] = [];
      groups[p.uzum_product_id].push(p);
    });

    return Object.entries(groups).filter(([pid, skus]) => {
      // Search filter
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        const match = skus.some(s =>
          (s.title || '').toLowerCase().includes(term) ||
          (s.sku_code || '').toLowerCase().includes(term) ||
          String(s.uzum_product_id).includes(term)
        );
        if (!match) return false;
      }
      // Stock filter
      const totalStock = skus.reduce((sum, s) => sum + (s.fbo_stock || 0) + (s.fbs_stock || 0), 0);
      if (stockFilter === 'instock' && totalStock === 0) return false;
      if (stockFilter === 'out' && totalStock > 0) return false;
      return true;
    });
  }, [products, searchTerm, stockFilter]);

  const totalPages = Math.ceil(filteredGroups.length / itemsPerPage);
  const paginatedGroups = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredGroups.slice(start, start + itemsPerPage);
  }, [filteredGroups, currentPage]);

  useEffect(() => { setCurrentPage(1); }, [searchTerm, stockFilter]);

  const toggleGroup = (pid: string) => {
    setExpandedGroups(prev => ({ ...prev, [pid]: !prev[pid] }));
  };

  // Stats
  const totalSkus = products.length;
  const totalStock = products.reduce((s, p) => s + (p.fbo_stock || 0) + (p.fbs_stock || 0), 0);
  const outOfStockSkus = products.filter(p => (p.fbo_stock || 0) + (p.fbs_stock || 0) === 0).length;
  const inStockSkus = totalSkus - outOfStockSkus;
  const shopLabel = selectedShop ? selectedShop.name : "Barcha do'konlar";

  return (
    <div className="flex flex-col gap-6">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">Mahsulotlar</h1>
          <p className="text-[var(--text-secondary)] mt-1 flex items-center gap-2 text-sm">
            <Store size={14} className="text-[var(--accent)]" />
            {shopLabel} — {filteredGroups.length} tovar ({totalSkus} SKU)
          </p>
        </div>
        <button onClick={handleSync} disabled={loading}
          className="flex items-center gap-2 bg-[var(--accent)] hover:opacity-90 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl font-semibold transition-all text-sm">
          <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Sinxronlash
        </button>
      </header>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-xs text-[var(--text-secondary)] mb-1">Jami SKU</p>
          <p className="text-2xl font-bold text-[var(--accent)]">{totalSkus.toLocaleString()}</p>
          <p className="text-[10px] text-[var(--text-secondary)]">{filteredGroups.length} ta tovar</p>
        </div>
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-xs text-[var(--text-secondary)] mb-1 flex items-center gap-1"><TrendingUp size={12} className="text-[#10b981]" /> Sotuvda</p>
          <p className="text-2xl font-bold text-[#10b981]">{inStockSkus.toLocaleString()}</p>
        </div>
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-xs text-[var(--text-secondary)] mb-1 flex items-center gap-1"><TrendingDown size={12} className="text-[#ef4444]" /> Tugagan</p>
          <p className="text-2xl font-bold text-[#ef4444]">{outOfStockSkus.toLocaleString()}</p>
        </div>
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4">
          <p className="text-xs text-[var(--text-secondary)] mb-1">Umumiy zaxira</p>
          <p className="text-2xl font-bold text-[#3b82f6]">{totalStock.toLocaleString()}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-4 flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[250px] relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" size={16} />
          <input type="text" placeholder="Nomi, SKU kodi bo'yicha qidirish..."
            className="w-full bg-[var(--background)] border border-[var(--border)] rounded-lg py-2 pl-9 pr-4 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] transition-all"
            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} />
        </div>
        <div className="flex gap-2">
          {[
            { key: 'all', label: 'Barchasi', count: products.length },
            { key: 'instock', label: 'Sotuvda', count: inStockSkus },
            { key: 'out', label: 'Tugagan', count: outOfStockSkus },
          ].map(f => (
            <button key={f.key} onClick={() => setStockFilter(f.key as any)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                stockFilter === f.key ? 'bg-[var(--accent)] text-white'
                  : 'bg-[var(--background)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border)]'
              }`}>{f.label} ({f.count})</button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-[var(--surface)] border border-[var(--border)] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[var(--border)]">
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase w-10"></th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase w-10">#</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase">Tovar</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-center">SKU soni</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-right">Tannarx</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-right">Narx</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-right">Marja</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-center">FBO</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-center">FBS</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-center">Jami</th>
                <th className="px-4 py-3 text-[10px] font-semibold text-[var(--text-secondary)] uppercase text-center">Holat</th>
              </tr>
            </thead>
            <tbody>
              {loading && products.length === 0 ? (
                <tr><td colSpan={11} className="px-4 py-20 text-center text-[var(--text-secondary)]">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-[var(--accent)]" /><span className="text-sm">Yuklanmoqda...</span>
                </td></tr>
              ) : paginatedGroups.length === 0 ? (
                <tr><td colSpan={11} className="px-4 py-20 text-center text-[var(--text-secondary)]">
                  <Package className="w-12 h-12 mx-auto mb-2 opacity-20" /><span className="text-sm">Mahsulotlar topilmadi</span>
                </td></tr>
              ) : (
                paginatedGroups.map(([pid, skus]: any, index: number) => {
                  const main = skus[0];
                  const totalFbo = skus.reduce((s: number, p: any) => s + (p.fbo_stock || 0), 0);
                  const totalFbs = skus.reduce((s: number, p: any) => s + (p.fbs_stock || 0), 0);
                  const stock = totalFbo + totalFbs;
                  const isOut = stock === 0;
                  const isOpen = expandedGroups[pid];

                  return (
                    <React.Fragment key={pid}>
                      {/* Guruh qatori */}
                      <tr className="hover:bg-[var(--surface-hover)] transition-all cursor-pointer border-b border-[var(--border)]"
                        onClick={() => toggleGroup(pid)}>
                        <td className="px-4 py-3 text-center">
                          {isOpen
                            ? <ChevronDown size={14} className="text-[var(--accent)]" />
                            : <ChevronRight size={14} className="text-[var(--text-secondary)]" />
                          }
                        </td>
                        <td className="px-4 py-3 text-xs text-[var(--text-secondary)] font-mono">
                          {(currentPage - 1) * itemsPerPage + index + 1}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg overflow-hidden bg-white border border-[var(--border)] flex-shrink-0 p-0.5">
                              <img src={`${API_BASE_URL}/api/products/image-proxy?url=${encodeURIComponent(main.image_url || '')}`}
                                alt="" className="w-full h-full object-contain" loading="lazy" />
                            </div>
                            <span className="text-sm font-semibold text-[var(--text-primary)] truncate max-w-[300px]" title={main.title}>
                              {main.title}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className="text-xs font-bold bg-[var(--accent)]/10 text-[var(--accent)] px-2 py-0.5 rounded-full">
                            {skus.length} SKU
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {main.purchase_price ? (
                            <span className="text-sm font-semibold text-[var(--text-secondary)]">{Number(main.purchase_price).toLocaleString()}</span>
                          ) : (
                            <span className="text-sm text-[var(--text-secondary)] opacity-40">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-sm font-semibold text-[var(--text-primary)]">{(main.price || 0).toLocaleString()}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {main.purchase_price && main.price ? (() => {
                            const margin = ((main.price - main.purchase_price) / main.price) * 100;
                            const color = margin >= 30 ? '#10b981' : margin >= 10 ? '#f59e0b' : '#ef4444';
                            return <span className="text-xs font-bold" style={{ color }}>{margin.toFixed(1)}%</span>;
                          })() : (
                            <span className="text-xs text-[var(--text-secondary)] opacity-40">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center font-bold text-sm text-[var(--text-primary)]">{totalFbo}</td>
                        <td className="px-4 py-3 text-center font-bold text-sm text-[var(--text-primary)]">{totalFbs}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`font-black text-sm ${isOut ? 'text-[#ef4444]' : 'text-[var(--accent)]'}`}>{stock}</span>
                        </td>
                        <td className="px-4 py-3 text-center">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            isOut ? 'bg-[#ef4444]/10 text-[#ef4444]' : 'bg-[#10b981]/10 text-[#10b981]'
                          }`}>{isOut ? 'Tugagan' : 'Sotuvda'}</span>
                        </td>
                      </tr>

                      {/* Ochilgan SKU qatorlari */}
                      {isOpen && skus.map((sku: any) => {
                        const skuStock = (sku.fbo_stock || 0) + (sku.fbs_stock || 0);
                        return (
                          <tr key={sku.id} className="bg-[var(--background)]/50 border-b border-[var(--border)]/50">
                            <td></td>
                            <td></td>
                            <td className="px-4 py-2 pl-16">
                              <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded overflow-hidden bg-white border border-[var(--border)] flex-shrink-0 p-0.5">
                                  <img src={`${API_BASE_URL}/api/products/image-proxy?url=${encodeURIComponent(sku.image_url || '')}`}
                                    alt="" className="w-full h-full object-contain" loading="lazy" />
                                </div>
                                <div className="flex flex-col">
                                  <span className="text-xs text-[var(--text-secondary)] truncate max-w-[250px]">{sku.title}</span>
                                  <code className="text-[9px] text-[var(--accent)] opacity-70">{sku.sku_code}</code>
                                </div>
                              </div>
                            </td>
                            <td></td>
                            <td className="px-4 py-2 text-right text-xs text-[var(--text-secondary)]">
                              {sku.purchase_price ? `${Number(sku.purchase_price).toLocaleString()} so'm` : <span className="opacity-40">—</span>}
                            </td>
                            <td className="px-4 py-2 text-right text-xs text-[var(--text-secondary)]">
                              {(sku.price || 0).toLocaleString()} so'm
                            </td>
                            <td className="px-4 py-2 text-right text-xs">
                              {sku.purchase_price && sku.price ? (() => {
                                const margin = ((sku.price - sku.purchase_price) / sku.price) * 100;
                                const color = margin >= 30 ? '#10b981' : margin >= 10 ? '#f59e0b' : '#ef4444';
                                return <span className="font-semibold" style={{ color }}>{margin.toFixed(1)}%</span>;
                              })() : <span className="opacity-40">—</span>}
                            </td>
                            <td className="px-4 py-2 text-center text-xs text-[var(--text-secondary)]">{sku.fbo_stock || 0}</td>
                            <td className="px-4 py-2 text-center text-xs text-[var(--text-secondary)]">{sku.fbs_stock || 0}</td>
                            <td className="px-4 py-2 text-center text-xs font-bold text-[var(--text-secondary)]">{skuStock}</td>
                            <td className="px-4 py-2 text-center">
                              <span className={`text-[9px] ${skuStock === 0 ? 'text-[#ef4444]' : 'text-[#10b981]'}`}>
                                {skuStock === 0 ? '✕' : '✓'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-[var(--border)] flex items-center justify-between">
            <span className="text-xs text-[var(--text-secondary)]">
              Sahifa <span className="font-bold text-[var(--accent)]">{currentPage}</span> / {totalPages}
              <span className="ml-2 opacity-60">({filteredGroups.length} tovar, {totalSkus} SKU)</span>
            </span>
            <div className="flex items-center gap-1">
              <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}
                className="w-8 h-8 rounded-lg flex items-center justify-center border border-[var(--border)] hover:border-[var(--accent)] transition-all disabled:opacity-20 text-[var(--text-secondary)]">
                <ChevronRight className="w-4 h-4 rotate-180" />
              </button>
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                let p = i + 1;
                if (totalPages > 7 && currentPage > 4) { p = currentPage - 3 + i; if (p > totalPages) p = totalPages - (6 - i); }
                if (p <= 0) return null;
                return (
                  <button key={p} onClick={() => setCurrentPage(p)}
                    className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                      currentPage === p ? 'bg-[var(--accent)] text-white' : 'text-[var(--text-secondary)] border border-[var(--border)] hover:border-[var(--accent)]'
                    }`}>{p}</button>
                );
              })}
              <button onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))} disabled={currentPage === totalPages}
                className="w-8 h-8 rounded-lg flex items-center justify-center border border-[var(--border)] hover:border-[var(--accent)] transition-all disabled:opacity-20 text-[var(--text-secondary)]">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
