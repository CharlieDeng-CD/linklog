import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LinkLog - Map Your Unknowns",
  description: "渐进式知识图谱生成器，帮你识别学习路径中的前置知识",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

