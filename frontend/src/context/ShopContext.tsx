'use client';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { apiUrl } from '@/lib/api';

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
  selectedShopId: number | null; // null = Barcha do'konlar
  setSelectedShopId: (id: number | null) => void;
  selectedShop: Shop | null;
  loading: boolean;
}

const ShopContext = createContext<ShopContextType>({
  shops: [],
  selectedShopId: null,
  setSelectedShopId: () => {},
  selectedShop: null,
  loading: true,
});

export function ShopProvider({ children }: { children: ReactNode }) {
  const [shops, setShops] = useState<Shop[]>([]);
  const [selectedShopId, setSelectedShopId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(apiUrl('/api/shops/'))
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setShops(data);
        }
      })
      .catch(err => console.error("Do'konlar yuklanmadi:", err))
      .finally(() => setLoading(false));
  }, []);

  const selectedShop = shops.find(s => s.id === selectedShopId) ?? null;

  return (
    <ShopContext.Provider value={{ shops, selectedShopId, setSelectedShopId, selectedShop, loading }}>
      {children}
    </ShopContext.Provider>
  );
}

export function useShop() {
  return useContext(ShopContext);
}
