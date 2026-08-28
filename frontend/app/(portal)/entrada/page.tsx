"use client";

import { CheckCircle2, Pencil, Plus, RefreshCw, Search, Trash2 } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Attendance, NamedEntity, StoreContext, User, YesNo } from "@/lib/types";
import { Button, Card, EmptyState, Field, PageHeader, SearchableSelect, StatusBadge } from "@/components/ui";

const today = new Date().toISOString().slice(0, 10);
const plans = [
  "Pre Pago",
  "Controle ate R$60,00",
  "Controle acima R$60,00",
  "Vivo Total",
  "Pos pago",
  "Fibra avulsa",
  "Outras Operadoras",
];
const saleReasonNames = new Set([
  "HABILITAÇÃO PRÉ/PÓS",
  "UPGRADE",
  "TOTALIZAÇÃO",
  "PRÉ PAGO",
  "OUTRAS OPERADORAS",
  "FIBRA AVULSA",
  "PJ",
]);
const initialForm = { password_number: "", cpf_cnpj: "", current_plan: "", ftth_available: "YES" as YesNo, available_for_sale: "YES" as YesNo, sale: "NO" as YesNo, reason_id: "", consultant_id: "" };

function YesNoField({ label, name, value, onChange }: { label: string; name: string; value: YesNo; onChange: (value: YesNo) => void }) {
  return <Field label={label} htmlFor={`${name}-yes`} required><div className="segmented" role="group" aria-label={label}><button id={`${name}-yes`} type="button" className="segment" aria-pressed={value === "YES"} onClick={() => onChange("YES")}>Sim</button><button type="button" className="segment" aria-pressed={value === "NO"} onClick={() => onChange("NO")}>Não</button></div></Field>;
}

export default function EntryPage() {
  const [date, setDate] = useState(today);
  const [regional, setRegional] = useState(""); const [coordinator, setCoordinator] = useState(""); const [store, setStore] = useState("");
  const [regionals, setRegionals] = useState<NamedEntity[]>([]); const [coordinators, setCoordinators] = useState<NamedEntity[]>([]); const [stores, setStores] = useState<NamedEntity[]>([]); const [consultants, setConsultants] = useState<NamedEntity[]>([]); const [reasons, setReasons] = useState<NamedEntity[]>([]);
  const [storeContext, setStoreContext] = useState<StoreContext | null>(null);
  const [form, setForm] = useState(initialForm); const [items, setItems] = useState<Attendance[]>([]);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState(""); const [search, setSearch] = useState(""); const [editing, setEditing] = useState<number | null>(null);

  useEffect(() => { Promise.all([api<NamedEntity[]>("/catalog/regionals"), api<NamedEntity[]>("/catalog/reasons"), api<User>("/me")]).then(([a, b, profile]) => { setRegionals(a); setReasons(b); if (profile.store_context) { setStoreContext(profile.store_context); setRegional(profile.store_context.regional_id.toString()); setCoordinator(profile.store_context.coordinator_id.toString()); setStore(profile.store_context.store_id.toString()); } }); }, []);
  useEffect(() => { if (!storeContext) { setCoordinator(""); setStore(""); } api<NamedEntity[]>(`/catalog/coordinators${regional ? `?regional_id=${regional}` : ""}`).then(setCoordinators); }, [regional, storeContext]);
  useEffect(() => { if (!storeContext) setStore(""); api<NamedEntity[]>(`/catalog/stores${coordinator ? `?coordinator_id=${coordinator}` : ""}`).then(setStores); }, [coordinator, storeContext]);
  useEffect(() => { setForm((old) => ({ ...old, consultant_id: "" })); if (store) api<NamedEntity[]>(`/catalog/consultants?store_id=${store}`).then(setConsultants); else setConsultants([]); }, [store]);

  const loadDay = useCallback(async () => {
    if (!store) { setItems([]); return; }
    const list = await api<{ items: Attendance[] }>(`/attendances?start_date=${date}&end_date=${date}&store_id=${store}&page_size=200`);
    setItems(list.items);
  }, [date, store]);
  useEffect(() => { loadDay().catch((reason) => setError(reason.message)); }, [loadDay]);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) { setForm((old) => ({ ...old, [key]: value })); }
  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    if (!regional || !coordinator || !store) { setError("Selecione Regional, Coordenador e Loja."); return; }
    if (!form.reason_id) { setError(`Selecione o motivo ${form.sale === "YES" ? "da venda" : "da não venda"}.`); return; }
    setBusy(true);
    try {
      const payload = { ...form, password_number: Number(form.password_number), reason_id: Number(form.reason_id), consultant_id: Number(form.consultant_id) };
      if (editing) await api(`/attendances/${editing}`, { method: "PATCH", body: JSON.stringify(payload) });
      else await api("/attendances", { method: "POST", body: JSON.stringify({ ...payload, date, regional_id: Number(regional), coordinator_id: Number(coordinator), store_id: Number(store) }) });
      setForm(initialForm); setEditing(null); setNotice(editing ? "Atendimento atualizado." : "Atendimento registrado."); await loadDay();
      window.setTimeout(() => setNotice(""), 4000);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar."); }
    finally { setBusy(false); }
  }
  function edit(item: Attendance) { setEditing(item.id); setForm({ password_number: item.password_number.toString(), cpf_cnpj: item.cpf_cnpj, current_plan: item.current_plan ?? "", ftth_available: item.ftth_available, available_for_sale: item.available_for_sale, sale: item.sale, reason_id: item.reason_id?.toString() ?? "", consultant_id: item.consultant_id.toString() }); window.scrollTo({ top: 0, behavior: "smooth" }); }
  async function remove(item: Attendance) { if (!window.confirm(`Excluir a senha ${item.password_number}? Esta ação ficará registrada na auditoria.`)) return; try { await api(`/attendances/${item.id}`, { method: "DELETE" }); await loadDay(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível excluir."); } }

  const consultantName = useMemo(() => Object.fromEntries(consultants.map((item) => [item.id, item.name])), [consultants]);
  const reasonName = useMemo(() => Object.fromEntries(reasons.map((item) => [item.id, item.name])), [reasons]);
  const visibleReasons = reasons.filter((item) => form.sale === "YES" ? saleReasonNames.has(item.name) : !saleReasonNames.has(item.name));
  const filtered = items.filter((item) => `${item.password_number} ${item.cpf_cnpj} ${consultantName[item.consultant_id] ?? ""}`.toLowerCase().includes(search.toLowerCase()));
  return <>
    <PageHeader eyebrow="Operação do dia" title="Entrada de dados" description="Registre cada atendimento com poucos cliques. A estrutura selecionada permanece para o próximo lançamento." />
    <Card><div className="card-body">
      <div className="context-grid">
        <Field label="Data" htmlFor="entry-date" required><input id="entry-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} /></Field>
        <Field label="Regional" htmlFor="entry-regional" required>{storeContext ? <input id="entry-regional" value={storeContext.regional_name} readOnly /> : <SearchableSelect id="entry-regional" value={regional} onChange={setRegional} options={regionals.map((item) => ({ value: String(item.id), label: item.name }))} required />}</Field>
        <Field label="Coordenador" htmlFor="entry-coordinator" required>{storeContext ? <input id="entry-coordinator" value={storeContext.coordinator_name} readOnly /> : <SearchableSelect id="entry-coordinator" value={coordinator} onChange={setCoordinator} disabled={!regional} options={coordinators.map((item) => ({ value: String(item.id), label: item.name }))} required />}</Field>
        <Field label="Loja" htmlFor="entry-store" required>{storeContext ? <input id="entry-store" value={storeContext.store_name} readOnly /> : <SearchableSelect id="entry-store" value={store} onChange={setStore} disabled={!coordinator} options={stores.map((item) => ({ value: String(item.id), label: item.name }))} required />}</Field>
      </div>
      <div className="section-divider"><span>{editing ? "Editando atendimento" : "Novo atendimento"}</span></div>
      <form onSubmit={submit}>
        <div className="form-grid">
          <Field label="Senha" htmlFor="password-number" required><input id="password-number" type="number" min="1" value={form.password_number} onChange={(e) => update("password_number", e.target.value)} inputMode="numeric" required /></Field>
          <Field label="CPF/CNPJ" htmlFor="cpf" hint="Zeros à esquerda serão preservados." required><input id="cpf" value={form.cpf_cnpj} onChange={(e) => update("cpf_cnpj", e.target.value)} inputMode="numeric" autoComplete="off" maxLength={18} required /></Field>
          <Field label="Plano atual" htmlFor="plan"><SearchableSelect id="plan" value={form.current_plan} onChange={(value) => update("current_plan", value)} options={plans.map((plan) => ({ value: plan, label: plan }))} /></Field>
          <Field label="Consultor" htmlFor="entry-consultant" required><SearchableSelect id="entry-consultant" value={form.consultant_id} onChange={(value) => update("consultant_id", value)} disabled={!store} options={consultants.map((item) => ({ value: String(item.id), label: item.name }))} required /></Field>
          <Field label={form.sale === "YES" ? "Motivo da venda" : "Motivo da não venda"} htmlFor="reason" required><SearchableSelect id="reason" value={form.reason_id} onChange={(value) => update("reason_id", value)} options={visibleReasons.map((item) => ({ value: String(item.id), label: item.name }))} required /></Field>
          <YesNoField label="Possui disponibilidade FTTH?" name="ftth" value={form.ftth_available} onChange={(value) => update("ftth_available", value)} />
          <YesNoField label="Disponível para venda?" name="available" value={form.available_for_sale} onChange={(value) => update("available_for_sale", value)} />
          <YesNoField label="Venda realizada?" name="sale" value={form.sale} onChange={(value) => { update("sale", value); update("reason_id", ""); }} />
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="form-actions">{editing && <Button type="button" variant="ghost" onClick={() => { setEditing(null); setForm(initialForm); }}>Cancelar edição</Button>}<Button type="submit" busy={busy} disabled={!store}><Plus size={18} /> {editing ? "Salvar alterações" : "Registrar atendimento"}</Button></div>
      </form>
    </div></Card>
    {notice && <div className="toast" role="status"><CheckCircle2 size={19} />{notice}</div>}
    <Card style={{ marginTop: 22 }}><div className="card-header"><div><h2>Atendimentos do dia</h2><p>{items.length} registro{items.length === 1 ? "" : "s"} na loja selecionada</p></div><div className="table-search"><Search size={17}/><input aria-label="Pesquisar atendimentos" placeholder="Senha, CPF/CNPJ ou consultor" value={search} onChange={(e) => setSearch(e.target.value)} /></div></div>
      {filtered.length ? <div className="table-wrap"><table><thead><tr><th>Senha</th><th>CPF/CNPJ</th><th>Plano</th><th>FTTH</th><th>Disp. venda</th><th>Venda</th><th>Motivo</th><th>Consultor</th><th>Horário</th><th>Ações</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td className="numeric"><strong>{item.password_number.toString().padStart(3,"0")}</strong></td><td className="numeric">{item.cpf_cnpj}</td><td>{item.current_plan || "—"}</td><td><StatusBadge value={item.ftth_available}/></td><td><StatusBadge value={item.available_for_sale}/></td><td><StatusBadge value={item.sale}/></td><td>{item.reason_id ? reasonName[item.reason_id] : "—"}</td><td>{consultantName[item.consultant_id] ?? "—"}</td><td className="numeric">{new Date(item.created_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</td><td><div className="row-actions"><button onClick={() => edit(item)} aria-label={`Editar senha ${item.password_number}`}><Pencil size={16}/></button><button className="danger" onClick={() => remove(item)} aria-label={`Excluir senha ${item.password_number}`}><Trash2 size={16}/></button></div></td></tr>)}</tbody></table></div> : <EmptyState title={store ? "Nenhum atendimento encontrado" : "Selecione uma loja"} description={store ? "Registre o primeiro atendimento ou ajuste a pesquisa." : "Os atendimentos do dia aparecerão aqui."} />}
      {store && <div className="table-footer"><Button variant="ghost" onClick={loadDay}><RefreshCw size={16}/> Atualizar lista</Button></div>}
    </Card>
  </>;
}
