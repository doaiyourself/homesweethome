import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "신혼집 매물 추천",
  description: "구로/양천/영등포 전월세 매물 자동 추천",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
