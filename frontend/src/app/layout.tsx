import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Sidebar from '@/components/Sidebar'
import { ShopProvider } from '@/context/ShopContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Uzum Analytics',
  description: 'Uzum Market sotuvchilari uchun analitika',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="uz">
      <body className={inter.className}>
        <ShopProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 ml-[260px] p-8 bg-[var(--background)] transition-colors duration-300">
              {children}
            </main>
          </div>
        </ShopProvider>
      </body>
    </html>
  )
}

