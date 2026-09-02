"use client";

import { ChevronLeft, ChevronRight, Download, Search } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api, download } from "@/lib/api";
import { localDateInputValue } from "@/lib/date";
import type { Attendance, NamedEntity } from "@/lib/types";
import { Button, Card, EmptyState, Field, PageHeader, SearchableSelect } from "@/components/ui";

const today = localDateInputValue();
const monthStart = localDateInputValue(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
const saleStatuses = ["Aguardando Instalação", "Instalada", "Cancelada", "Reagendada", "Pendência"];

export default function ManagementPage() {
  const [start, setStart] = useState(monthStart); const [end, setEnd] = useState(today); const [store, setStore] = useState(""); const [consultant, setConsultant] = useState(""); const [status, setStatus] = useState(""); const [document, setDocument] = useState("");
  const [stores, setStores] = useState<NamedEntity[]>([]); const [consultants, setConsultants] = useState<NamedEntity[]>([]);
  const [items, setItems] = useState<Attendance[]>([]); const [total, setTotal] = useState(0); const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false); const [error, setError] = useState(""); const [saving, setSaving] = useState<number | null>(null);
  useEffect(() => { api<NamedEntity[]>("/catalog/stores").then(setStores); }, []);
  useEffect(() => { setConsultant(""); if (store) api<NamedEntity[]>(`/catalog/consultants?store_id=${store}`).then(setConsultants); else setConsultants([]); }, [store]);
  const query = useMemo(() => {
    const params = new URLSearchParams({ start_date: start, end_date: end, sale: "YES", page: String(page), page_size: "25" });
    if (store) params.set("store_id", store);
    if (consultant) params.set("consultant_id", consultant);
    if (status) params.set("sale_status", status);
    if (document) params.set("cpf_cnpj", document);
    return params.toString();
  }, [start, end, store, consultant, status, document, page]);
  const load = useCallback(async (event?: FormEvent) => {
    event?.preventDefault(); setLoading(true); setError("");
    try {
      const result = await api<{ items: Attendance[]; total: number }>(`/attendances?${query}`);
      setItems(result.items); setTotal(result.total);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha na consulta."); }
    finally { setLoading(false); }
  }, [query]);
  useEffect(() => { load(); }, [load]);
  const names = useMemo(() => Object.fromEntries(consultants.map((item) => [item.id, item.name])), [consultants]);
  const pages = Math.max(1, Math.ceil(total / 25));
  async function changeStatus(item: Attendance, value: string) {
    setSaving(item.id); setError("");
    try {
      const updated = await api<Attendance>(`/attendances/${item.id}`, { method: "PATCH", body: JSON.stringify({ sale_status: value }) });
      setItems((current) => current.map((row) => row.id === item.id ? { ...row, sale_status: updated.sale_status } : row));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível atualizar o status."); }
    finally { setSaving(null); }
  }
  return <>
    <PageHeader eyebrow="Base única" title="Gerenciamento somente venda" description="Acompanhe pedidos vendidos e atualize o status da instalação." action={<Button variant="secondary" onClick={() => download(`/exports/attendances.xlsx?start_date=${start}&end_date=${end}&sale=YES${store ? `&store_id=${store}` : ""}${consultant ? `&consultant_id=${consultant}` : ""}`, "vendas.xlsx")}><Download size={17}/> Exportar Excel</Button>} />
    <form onSubmit={(event) => { setPage(1); load(event); }}><Card className="filters history-filters">
      <Field label="Data inicial" htmlFor="management-start"><input id="management-start" type="date" value={start} onChange={(event) => setStart(event.target.value)} /></Field>
      <Field label="Data final" htmlFor="management-end"><input id="management-end" type="date" value={end} onChange={(event) => setEnd(event.target.value)} /></Field>
      <Field label="Loja" htmlFor="management-store"><SearchableSelect id="management-store" value={store} onChange={setStore} placeholder="Todas" options={stores.map((item) => ({ value: String(item.id), label: item.name }))} /></Field>
      <Field label="Consultor" htmlFor="management-consultant"><SearchableSelect id="management-consultant" value={consultant} onChange={setConsultant} disabled={!store} placeholder="Todos" options={consultants.map((item) => ({ value: String(item.id), label: item.name }))} /></Field>
      <Field label="Status" htmlFor="management-status"><SearchableSelect id="management-status" value={status} onChange={setStatus} placeholder="Todos" options={saleStatuses.map((item) => ({ value: item, label: item }))} /></Field>
      <Field label="CPF/CNPJ" htmlFor="management-doc"><input id="management-doc" value={document} onChange={(event) => setDocument(event.target.value)} inputMode="numeric" placeholder="Pesquisar documento" /></Field>
      <Button type="submit" busy={loading}><Search size={17}/> Consultar</Button>
    </Card></form>
    {error && <p className="form-error" role="alert">{error}</p>}
    <Card>
      <div className="card-header"><div><h2>Vendas encontradas</h2><p>{total.toLocaleString("pt-BR")} venda{total === 1 ? "" : "s"}</p></div></div>
      {items.length ? <div className="table-wrap"><table><thead><tr><th>Data</th><th>Senha</th><th>CPF/CNPJ</th><th>Plano</th><th>Ordem</th><th>Classificação final</th><th>Consultor</th><th>Status</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}>
        <td>{item.date.split("-").reverse().join("/")}</td>
        <td className="numeric">{item.password_number.toString().padStart(3, "0")}</td>
        <td className="numeric">{item.cpf_cnpj}</td>
        <td>{item.current_plan || "—"}</td>
        <td className="numeric">{item.order_number || "—"}</td>
        <td>{item.outcome_detail || "—"}</td>
        <td>{names[item.consultant_id] ?? `#${item.consultant_id}`}</td>
        <td><select className="status-select" value={item.sale_status || "Aguardando Instalação"} disabled={saving === item.id} aria-label={`Status da senha ${item.password_number}`} onChange={(event) => changeStatus(item, event.target.value)}>{saleStatuses.map((option) => <option key={option} value={option}>{option}</option>)}</select></td>
      </tr>)}</tbody></table></div> : <EmptyState title="Nenhuma venda encontrada" description="Ajuste o período ou o status para consultar outros pedidos." />}
      <div className="pagination"><span>Página {page} de {pages}</span><div><button aria-label="Página anterior" disabled={page <= 1} onClick={() => setPage((old) => old - 1)}><ChevronLeft size={18}/></button><button aria-label="Próxima página" disabled={page >= pages} onClick={() => setPage((old) => old + 1)}><ChevronRight size={18}/></button></div></div>
    </Card>
  </>;
}
