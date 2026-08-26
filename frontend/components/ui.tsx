"use client";

import { Check, ChevronDown, LoaderCircle, Search } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";
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

export type SelectOption = { value: string; label: string };

export function SearchableSelect({ id, value, onChange, options, placeholder = "Selecione", disabled, required }: { id: string; value: string; onChange: (value: string) => void; options: SelectOption[]; placeholder?: string; disabled?: boolean; required?: boolean }) {
  const [open, setOpen] = useState(false); const [query, setQuery] = useState("");
  const root = useRef<HTMLDivElement>(null); const searchId = useId();
  const selected = options.find((item) => item.value === value);
  const visible = useMemo(() => options.filter((item) => item.label.toLocaleLowerCase("pt-BR").includes(query.toLocaleLowerCase("pt-BR"))), [options, query]);
  useEffect(() => { const close = (event: MouseEvent) => { if (!root.current?.contains(event.target as Node)) setOpen(false); }; document.addEventListener("mousedown", close); return () => document.removeEventListener("mousedown", close); }, []);
  useEffect(() => { if (!open) setQuery(""); }, [open]);
  return <div className="searchable-select" ref={root}>
    <button id={id} type="button" className="searchable-select-trigger" disabled={disabled} aria-haspopup="listbox" aria-expanded={open} aria-controls={`${id}-options`} aria-required={required} onClick={() => setOpen((current) => !current)}>
      <span className={selected ? "" : "placeholder"}>{selected?.label ?? placeholder}</span><ChevronDown size={17} aria-hidden="true" />
    </button>
    {open && <div className="searchable-select-menu"><label className="sr-only" htmlFor={searchId}>Buscar opções</label><div className="searchable-select-search"><Search size={16} aria-hidden="true" /><input id={searchId} autoFocus value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Escape") setOpen(false); }} placeholder="Buscar..." /></div><div id={`${id}-options`} className="searchable-select-options" role="listbox" aria-labelledby={id}>
      <button type="button" role="option" aria-selected={!value} className={!value ? "selected" : ""} onClick={() => { onChange(""); setOpen(false); }}>{placeholder}</button>
      {visible.map((item) => <button type="button" key={item.value} role="option" aria-selected={item.value === value} className={item.value === value ? "selected" : ""} onClick={() => { onChange(item.value); setOpen(false); }}>{item.label}{item.value === value && <Check size={16} aria-hidden="true" />}</button>)}
      {!visible.length && <p>Nenhuma opção encontrada.</p>}
    </div></div>}
  </div>;
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
