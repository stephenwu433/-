import { ClerkProvider, Show, UserButton } from "@clerk/nextjs";
import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PlanFlow",
  description: "团队版项目组合与排期协作",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="zh-CN"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ClerkProvider>
          <header className="flex items-center justify-between border-b border-zinc-200 px-6 py-4">
            <Link
              href="/"
              className="text-lg font-semibold tracking-tight text-zinc-900"
            >
              PlanFlow
            </Link>
            <div className="flex items-center gap-3">
              <Show when="signed-in">
                <Link
                  href="/portfolio"
                  className="rounded-md px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100"
                >
                  项目总览
                </Link>
                <Link
                  href="/workload"
                  className="rounded-md px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100"
                >
                  跨项目负荷
                </Link>
                <Link
                  href="/teams"
                  className="rounded-md px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100"
                >
                  我的团队
                </Link>
                <UserButton />
              </Show>
              <Show when="signed-out">
                <Link
                  href="/sign-in"
                  className="rounded-md px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-100"
                >
                  登录
                </Link>
                <Link
                  href="/sign-up"
                  className="rounded-md bg-zinc-900 px-3 py-1.5 text-sm text-white hover:bg-zinc-800"
                >
                  注册
                </Link>
              </Show>
            </div>
          </header>
          {children}
        </ClerkProvider>
      </body>
    </html>
  );
}
