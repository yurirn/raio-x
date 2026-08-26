import { LoaderCircle } from "lucide-react";
import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description: string; action?: ReactNode }) {
  return <header className="page-header">
    <div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}
  </header>;
}

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return <section className={`card ${className}`} {...props} />;
}

export function Button({ children, busy, variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { busy?: boolean; variant?: "primary" | "secondary" | "ghost" | "danger" }) {
  return <button className={`button button-${variant}`} disabled={busy || props.disabled} {...props}>
    {busy && <LoaderCircle size={17} className="spin" aria-hidden="true" />}{children}
  </button>;
}

export function Field({ label, htmlFor, hint, required, children }: { label: string; htmlFor: string; hint?: string; required?: boolean; children: ReactNode }) {
  return <div className="field"><label htmlFor={htmlFor}>{label}{required && <span aria-hidden="true"> *</span>}</label>{children}{hint && <small>{hint}</small>}</div>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty-state"><div className="empty-mark" aria-hidden="true" /><strong>{title}</strong><p>{description}</p></div>;
}

export function Skeleton({ height = 120 }: { height?: number }) {
  return <div className="skeleton" style={{ height }} aria-label="Carregando conteúdo" />;
}

export function StatusBadge({ value }: { value: string | boolean }) {
  const positive = value === "YES" || value === true;
  return <span className={`status ${positive ? "status-positive" : "status-neutral"}`}><i />{positive ? "Sim" : "Não"}</span>;
}
