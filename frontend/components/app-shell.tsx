"use client";

import { Activity, BarChart3, Building2, ClipboardList, History, LogOut, Menu, Users, X } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, clearToken, getToken } from "@/lib/api";
import type { User } from "@/lib/types";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: Activity },
  { href: "/entrada", label: "Entrada de dados", icon: ClipboardList },
  { href: "/consolidado", label: "Consolidado", icon: BarChart3 },
  { href: "/historico", label: "Histórico", icon: History },
  { href: "/cadastros", label: "Cadastros", icon: Building2, admin: true },
  { href: "/usuarios", label: "Usuários", icon: Users, admin: true },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) { router.replace("/login"); return; }
    api<User>("/me").then(setUser).catch(() => router.replace("/login"));
  }, [router]);

  function logout() { clearToken(); router.replace("/login"); }

  if (!user) return <main className="boot-screen"><div className="brand-mark">RX</div><p>Preparando seu painel…</p></main>;
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Pular para o conteúdo</a>
    <aside className={`sidebar ${open ? "is-open" : ""}`} aria-label="Navegação principal">
      <div className="brand"><Image className="brand-vivo" src="/logo-vivo.webp" alt="Vivo" width={94} height={30} priority /></div>
      <button className="icon-button close-nav" onClick={() => setOpen(false)} aria-label="Fechar menu"><X size={21} /></button>
      <nav>{navigation.filter((item) => !item.admin || user.role === "ADMIN").map(({ href, label, icon: Icon }) =>
        <Link key={href} href={href} onClick={() => setOpen(false)} className={pathname.startsWith(href) ? "active" : ""}><Icon size={20} /><span>{label}</span></Link>)}</nav>
      <div className="sidebar-footer"><div className="avatar">{user.name.slice(0, 2).toUpperCase()}</div><div><strong>{user.name}</strong><small>{user.role === "ADMIN" ? "Administrador" : user.role === "COORDINATOR" ? "Coordenador" : "Operador"}</small></div><button className="icon-button" onClick={logout} aria-label="Sair"><LogOut size={19} /></button></div>
    </aside>
    {open && <button className="nav-scrim" onClick={() => setOpen(false)} aria-label="Fechar menu" />}
    <div className="app-content">
      <header className="mobile-header"><button className="icon-button" onClick={() => setOpen(true)} aria-label="Abrir menu"><Menu size={22} /></button><Image className="mobile-vivo" src="/logo-vivo.webp" alt="Vivo" width={74} height={24} /><span className="live-indicator"><i /> Online</span></header>
      <main id="main-content" tabIndex={-1}>{children}</main>
    </div>
  </div>;
}
