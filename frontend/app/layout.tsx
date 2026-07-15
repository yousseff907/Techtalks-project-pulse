import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Project Pulse",
  description: "One dashboard for every tool your team already uses.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-svh bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
