import "geist/font/sans";
import "geist/font/mono";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Raio X", template: "%s · Raio X" },
  description: "Gestão operacional de atendimentos e conversão",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
