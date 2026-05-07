'use client';
import {
  LayoutDashboard, ShoppingBag, Package, FileText, CreditCard,
  Settings, RefreshCcw, RotateCcw, Sun, Moon, Store, ChevronDown, CheckCircle2,
  BookOpen
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { useShop } from '@/context/ShopContext';

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/' },
  { icon: ShoppingBag, label: 'Buyurtmalar', href: '/orders' },
  { icon: Package, label: 'Mahsulotlar', href: '/products' },
  { icon: FileText, label: 'Yukxatlar', href: '/invoices' },
  { icon: RotateCcw, label: 'Qaytarishlar', href: '/returns' },
  { icon: CreditCard, label: 'Moliya', href: '/finance' },
  { icon: RefreshCcw, label: 'FBS', href: '/fbs' },
  { icon: BookOpen, label: 'API Hujjatlar', href: '/docs' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [theme, setTheme] = useState('dark');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { shops, selectedShopIds, toggleShop, selectAll, loading } = useShop();

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    if (savedTheme === 'light') {
      document.body.classList.add('light-theme');
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    if (newTheme === 'light') {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }
  };

  const selectedShopName = (() => {
    if (selectedShopIds.length === 0) return "Barcha do'konlar";
    if (selectedShopIds.length === 1) {
      return shops.find(s => s.id === selectedShopIds[0])?.name ?? "Do'kon tanlang";
    }
    return `${selectedShopIds.length} ta do'kon tanlangan`;
  })();
  const allSelected = selectedShopIds.length === 0;

  return (
    <aside className="w-[260px] h-screen bg-[var(--surface)] border-r border-[var(--border)] flex flex-col py-6 px-4 fixed left-0 top-0 transition-colors duration-300 overflow-y-auto">
      {/* Logo */}
      <div className="flex items-center gap-3 px-2 mb-6">
        <div className="w-8 h-8 bg-[var(--accent)] rounded-lg flex items-center justify-center font-extrabold text-white text-sm">
          U
        </div>
        <span className="text-lg font-bold text-[var(--text-primary)]">Uzum Analytics</span>
      </div>

      {/* Shop Selector */}
      <div className="mb-5 relative" ref={dropdownRef}>
        <button
          id="shop-selector-btn"
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="w-full flex items-center gap-2 px-3 py-2.5 bg-[var(--accent)]/10 border border-[var(--accent)]/30 rounded-xl text-[var(--text-primary)] hover:border-[var(--accent)] transition-all group"
        >
          <Store size={16} className="text-[var(--accent)] shrink-0" />
          <span className="flex-1 text-left text-sm font-medium truncate">
            {loading ? "Yuklanmoqda..." : selectedShopName}
          </span>
          <ChevronDown
            size={16}
            className={`text-[var(--text-secondary)] transition-transform duration-200 shrink-0 ${dropdownOpen ? 'rotate-180' : ''}`}
          />
        </button>

        {/* Dropdown */}
        {dropdownOpen && !loading && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-[var(--surface)] border border-[var(--border)] rounded-xl shadow-2xl shadow-black/40 z-50 overflow-hidden max-h-[400px] overflow-y-auto">
            {/* "Barcha do'konlar" — multi-select'ni tozalaydi */}
            <button
              id="shop-all-option"
              onClick={() => { selectAll(); }}
              className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm transition-all hover:bg-[var(--surface-hover)] ${
                allSelected
                  ? 'text-[var(--accent)] font-semibold bg-[var(--accent)]/5'
                  : 'text-[var(--text-secondary)]'
              }`}
            >
              <Store size={14} className="shrink-0" />
              <span className="flex-1 text-left">Barcha do'konlar</span>
              {allSelected && <CheckCircle2 size={14} className="text-[var(--accent)]" />}
            </button>

            {/* Divider */}
            <div className="border-t border-[var(--border)] mx-2 my-1" />

            {/* Multi-select shop list */}
            {shops.length === 0 ? (
              <div className="px-3 py-4 text-center text-xs text-[var(--text-secondary)]">
                Avval sinxronizatsiya qiling
              </div>
            ) : (
              shops.map(shop => {
                const isChecked = selectedShopIds.includes(shop.id);
                return (
                  <button
                    key={shop.id}
                    id={`shop-option-${shop.id}`}
                    onClick={() => { toggleShop(shop.id); }}
                    className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm transition-all hover:bg-[var(--surface-hover)] ${
                      isChecked
                        ? 'text-[var(--accent)] font-semibold'
                        : 'text-[var(--text-secondary)]'
                    }`}
                  >
                    {/* Checkbox */}
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 transition-all ${
                      isChecked
                        ? 'bg-[var(--accent)] border-[var(--accent)]'
                        : 'border-[var(--border)] bg-transparent'
                    }`}>
                      {isChecked && (
                        <svg width="10" height="10" viewBox="0 0 12 12" fill="none">
                          <path d="M2 6.5L4.5 9L10 3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                    <div className="w-5 h-5 rounded-md bg-[var(--accent)]/10 flex items-center justify-center shrink-0">
                      <span className="text-[9px] font-bold text-[var(--accent)]">
                        {shop.name.substring(0, 2).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 text-left min-w-0">
                      <div className="truncate font-medium">{shop.name}</div>
                      <div className="text-[10px] text-[var(--text-secondary)] flex gap-2">
                        <span>{shop.product_count} mahsulot</span>
                        <span>·</span>
                        <span>{shop.order_count} buyurtma</span>
                      </div>
                    </div>
                  </button>
                );
              })
            )}

            {/* Tagligida tanlanganlar soni */}
            {selectedShopIds.length > 0 && (
              <div className="border-t border-[var(--border)] px-3 py-2 text-[11px] text-[var(--text-secondary)] flex justify-between items-center bg-[var(--surface-hover)]/30">
                <span>{selectedShopIds.length} ta tanlangan</span>
                <button
                  onClick={() => selectAll()}
                  className="text-[var(--accent)] hover:underline"
                >
                  Tozalash
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive
                  ? 'bg-[var(--accent)]/10 text-[var(--accent)] font-semibold'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)]'
              }`}
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom */}
      <div className="mt-4 flex flex-col gap-1 pt-4 border-t border-[var(--border)]">
        <button
          id="theme-toggle-btn"
          onClick={toggleTheme}
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] transition-all"
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          <span>{theme === 'dark' ? 'Kun rejimi' : 'Tun rejimi'}</span>
        </button>

        <Link
          href="/settings"
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--surface-hover)] hover:text-[var(--text-primary)] transition-all"
        >
          <Settings size={20} />
          <span>Sozlamalar</span>
        </Link>
      </div>
    </aside>
  );
}
