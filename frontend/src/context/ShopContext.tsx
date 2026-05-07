'use client';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiUrl, authFetch } from '@/lib/api';

export interface Shop {
  id: number;
  uzum_shop_id: number | null;
  name: string;
  is_active: boolean;
  product_count: number;
  order_count: number;
}

interface ShopContextType {
  shops: Shop[];
  /** Tanlangan do'konlar IDlari. Bo'sh array = barcha do'konlar. */
  selectedShopIds: number[];
  setSelectedShopIds: (ids: number[]) => void;
  toggleShop: (id: number) => void;
  selectAll: () => void;
  /** Backward-compat: aniq 1 ta do'kon tanlangan bo'lsa shu, aks holda null */
  selectedShopId: number | null;
  selectedShop: Shop | null;
  loading: boolean;
}

const ShopContext = createContext<ShopContextType>({
  shops: [],
  selectedShopIds: [],
  setSelectedShopIds: () => {},
  toggleShop: () => {},
  selectAll: () => {},
  selectedShopId: null,
  selectedShop: null,
  loading: true,
});

const STORAGE_KEY = 'selectedShopIds';

export function ShopProvider({ children }: { children: ReactNode }) {
  const [shops, setShops] = useState<Shop[]>([]);
  const [selectedShopIds, setSelectedShopIdsState] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const arr = JSON.parse(saved);
        if (Array.isArray(arr) && arr.every(x => typeof x === 'number')) {
          setSelectedShopIdsState(arr);
        }
      }
    } catch {}

    authFetch(apiUrl('/api/shops/'))
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setShops(data);
        }
      })
      .catch(err => console.error("Do'konlar yuklanmadi:", err))
      .finally(() => setLoading(false));
  }, []);

  const setSelectedShopIds = (ids: number[]) => {
    setSelectedShopIdsState(ids);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(ids)); } catch {}
  };

  const toggleShop = (id: number) => {
    setSelectedShopIds(
      selectedShopIds.includes(id)
        ? selectedShopIds.filter(x => x !== id)
        : [...selectedShopIds, id]
    );
  };

  const selectAll = () => setSelectedShopIds([]);

  const selectedShopId = selectedShopIds.length === 1 ? selectedShopIds[0] : null;
  const selectedShop = selectedShopId !== null
    ? shops.find(s => s.id === selectedShopId) ?? null
    : null;

  return (
    <ShopContext.Provider value={{
      shops,
      selectedShopIds,
      setSelectedShopIds,
      toggleShop,
      selectAll,
      selectedShopId,
      selectedShop,
      loading,
    }}>
      {children}
    </ShopContext.Provider>
  );
}

export function useShop() {
  return useContext(ShopContext);
}
