import type { Metadata } from "next";

import { Header } from "@/components/Header";

import "./globals.css";

export const metadata: Metadata = {
  title: "신혼집 매물 추천",
  description: "구로·양천·영등포 전월세 매물 자동 추천",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="ko"
      className="bg-gray-50 text-gray-900 antialiased dark:bg-gray-950 dark:text-gray-100"
    >
      <body className="min-h-screen">
        <Header />
        <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
