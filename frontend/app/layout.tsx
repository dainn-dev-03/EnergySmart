import type { Metadata } from "next"
import { Geist_Mono, Inter } from "next/font/google"

import { Providers } from "@/components/providers"

import "./globals.css"

// Inter ships a Vietnamese subset (Geist does not, so diacritics would fall back to another font).
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "vietnamese"],
})

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: {
    default: "EnergySmart",
    template: "%s · EnergySmart",
  },
  description: "Quản lý và phân tích tiêu thụ điện năng cho tòa nhà",
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="vi" className={`${inter.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
