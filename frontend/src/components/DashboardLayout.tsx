import { ReactNode } from 'react'

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen bg-gray-100">
      <aside className="w-64 bg-white border-r">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-indigo-600">Uzum Analytics</h2>
        </div>
        <nav className="mt-6">
          <a href="#" className="flex items-center px-6 py-3 text-gray-700 bg-gray-100 border-l-4 border-indigo-600">
            <span className="font-semibold">Dashboard</span>
          </a>
          <a href="#" className="flex items-center px-6 py-3 text-gray-500 hover:bg-gray-50">
            <span className="font-semibold">Products</span>
          </a>
          <a href="#" className="flex items-center px-6 py-3 text-gray-500 hover:bg-gray-50">
            <span className="font-semibold">Orders</span>
          </a>
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-8">
        {children}
      </main>
    </div>
  )
}
