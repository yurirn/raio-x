"use client";

import { CheckCircle2, Pencil, Plus, RefreshCw, Search, Trash2, X } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { localDateInputValue } from "@/lib/date";
import type { Attendance, NamedEntity, StoreContext, UnusedPasswords, User, YesNo } from "@/lib/types";
import { Button, Card, EmptyState, Field, PageHeader, SearchableSelect, StatusBadge } from "@/components/ui";

const today = localDateInputValue();
const plans = [
  "Pre Pago",
  "Controle ate R$60,00",
  "Controle acima R$60,00",
  "Vivo Total",
  "Pos pago",
  "Fibra avulsa",
  "Outras Operadoras",
  "PJ",
];
const activities = ["Físico", "Mailing", "Não aguardou"];
const opportunities = ["Disp Venda", "Pinga Lote", "Alívio", "Cond Porta"];
const nonOpportunities = ["Dívida", "Fidelidade", "Fibra end", "Realta"];
const opportunityChoices = [
  { group: "Oport.", values: opportunities },
  { group: "Não oport.", values: nonOpportunities },
] as const;
const saleOutcomes = ["Fibra avulsa", "Vivo Total", "Totalização", "PJ"];
const nonSaleOutcomes = ["Não é decisor", "Não quer fibra", "Oferta concorrência", "PJ"];
const saleReasonNames = new Set([
  "HABILITAÇÃO PRÉ/PÓS",
  "UPGRADE",
  "TOTALIZAÇÃO",
  "PRÉ PAGO",
  "OUTRAS OPERADORAS",
  "FIBRA AVULSA",
  "PJ",
]);
const unusedPreviewLimit = 5;
const initialForm = { password_number: "", activity: "", cpf_cnpj: "", current_plan: "", opportunity: "", non_opportunity: "", ftth_available: "YES" as YesNo, available_for_sale: "YES" as YesNo, sale: "NO" as YesNo, order_number: "", outcome_detail: "", reason_id: "", consultant_id: "" };

function formatPassword(value: number) {
  return value.toString().padStart(3, "0");
}

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
  const [finalizationOpen, setFinalizationOpen] = useState(false);
  const [unusedOpen, setUnusedOpen] = useState(false);
  const [unused, setUnused] = useState<number[]>([]);

  useEffect(() => { Promise.all([api<NamedEntity[]>("/catalog/regionals"), api<NamedEntity[]>("/catalog/reasons"), api<User>("/me")]).then(([a, b, profile]) => { setRegionals(a); setReasons(b); if (profile.store_context) { setStoreContext(profile.store_context); setRegional(profile.store_context.regional_id.toString()); setCoordinator(profile.store_context.coordinator_id.toString()); setStore(profile.store_context.store_id.toString()); } }); }, []);
  useEffect(() => { if (!storeContext) { setCoordinator(""); setStore(""); } api<NamedEntity[]>(`/catalog/coordinators${regional ? `?regional_id=${regional}` : ""}`).then(setCoordinators); }, [regional, storeContext]);
  useEffect(() => { if (!storeContext) setStore(""); api<NamedEntity[]>(`/catalog/stores${coordinator ? `?coordinator_id=${coordinator}` : ""}`).then(setStores); }, [coordinator, storeContext]);
  useEffect(() => { setForm((old) => ({ ...old, consultant_id: "" })); if (store) api<NamedEntity[]>(`/catalog/consultants?store_id=${store}`).then(setConsultants); else setConsultants([]); }, [store]);

  const loadDay = useCallback(async () => {
    if (!store) { setItems([]); setUnused([]); return; }
    const [list, pending] = await Promise.all([
      api<{ items: Attendance[] }>(`/attendances?start_date=${date}&end_date=${date}&store_id=${store}&page_size=200`),
      api<UnusedPasswords>(`/attendances/unused-passwords?date=${date}&store_id=${store}`),
    ]);
    setItems(list.items);
    setUnused(pending.items);
  }, [date, store]);
  useEffect(() => { loadDay().catch((reason) => setError(reason.message)); }, [loadDay]);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) { setForm((old) => ({ ...old, [key]: value })); }
  function selectClassification(value: string) {
    const isOpportunity = opportunities.includes(value);
    setForm((old) => ({ ...old, opportunity: isOpportunity ? value : "", non_opportunity: isOpportunity ? "" : value }));
  }
  function legacyRecord() { return Boolean(editing && !form.activity && !form.opportunity && !form.non_opportunity && !form.order_number && !form.outcome_detail); }
  function validateEntry() {
    if (!regional || !coordinator || !store) { setError("Selecione Regional, Coordenador e Loja."); return false; }
    if (!legacyRecord() && !form.activity) { setError("Selecione a atuação."); return false; }
    if (!legacyRecord() && Boolean(form.opportunity) === Boolean(form.non_opportunity)) { setError("Selecione uma classificação."); return false; }
    return true;
  }
  function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    if (!validateEntry()) return;
    if (legacyRecord()) { void saveAttendance(); return; }
    setFinalizationOpen(true);
  }
  async function saveAttendance() {
    const isLegacyRecord = legacyRecord();
    setBusy(true);
    try {
      const payload = { ...form, password_number: Number(form.password_number), reason_id: Number(form.reason_id), consultant_id: Number(form.consultant_id) };
      const legacyPayload: Partial<typeof payload> = { ...payload };
      delete legacyPayload.activity;
      delete legacyPayload.opportunity;
      delete legacyPayload.non_opportunity;
      delete legacyPayload.order_number;
      delete legacyPayload.outcome_detail;
      const requestPayload = isLegacyRecord ? legacyPayload : payload;
      if (editing) await api(`/attendances/${editing}`, { method: "PATCH", body: JSON.stringify(requestPayload) });
      else await api("/attendances", { method: "POST", body: JSON.stringify({ ...requestPayload, date, regional_id: Number(regional), coordinator_id: Number(coordinator), store_id: Number(store) }) });
      setFinalizationOpen(false); setForm(initialForm); setEditing(null); setNotice(editing ? "Atendimento atualizado." : "Atendimento registrado."); await loadDay();
      window.setTimeout(() => setNotice(""), 4000);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível salvar."); }
    finally { setBusy(false); }
  }
  function finalize(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!form.reason_id) { setError(`Selecione o motivo ${form.sale === "YES" ? "da venda" : "da não venda"}.`); return; }
    if (form.sale === "YES" && !form.order_number) { setError("Informe o número da ordem para finalizar a venda."); return; }
    if (!form.outcome_detail) { setError("Selecione a classificação final do atendimento."); return; }
    void saveAttendance();
  }
  function edit(item: Attendance) { setEditing(item.id); setForm({ password_number: item.password_number.toString(), activity: item.activity ?? "", cpf_cnpj: item.cpf_cnpj, current_plan: item.current_plan ?? "", opportunity: item.opportunity ?? "", non_opportunity: item.non_opportunity ?? "", ftth_available: item.ftth_available, available_for_sale: item.available_for_sale, sale: item.sale, order_number: item.order_number ?? "", outcome_detail: item.outcome_detail ?? "", reason_id: item.reason_id?.toString() ?? "", consultant_id: item.consultant_id.toString() }); window.scrollTo({ top: 0, behavior: "smooth" }); }
  async function remove(item: Attendance) { if (!window.confirm(`Excluir a senha ${item.password_number}? Esta ação ficará registrada na auditoria.`)) return; try { await api(`/attendances/${item.id}`, { method: "DELETE" }); await loadDay(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível excluir."); } }

  const consultantName = useMemo(() => Object.fromEntries(consultants.map((item) => [item.id, item.name])), [consultants]);
  const reasonName = useMemo(() => Object.fromEntries(reasons.map((item) => [item.id, item.name])), [reasons]);
  const visibleReasons = reasons.filter((item) => form.sale === "YES" ? saleReasonNames.has(item.name) : !saleReasonNames.has(item.name));
  const filtered = items.filter((item) => `${item.password_number} ${item.cpf_cnpj} ${consultantName[item.consultant_id] ?? ""}`.toLowerCase().includes(search.toLowerCase()));
  return <>
    <PageHeader eyebrow="Operação do dia" title="Entrada de dados" description="Registre cada atendimento com poucos cliques. A estrutura selecionada permanece para o próximo lançamento." action={store ? <aside className="unused-passwords" aria-live="polite"><div className="unused-passwords-head"><span>Senhas não usadas</span><strong>{unused.length}</strong></div>{unused.length ? <p className="unused-passwords-list">{unused.slice(0, unusedPreviewLimit).map(formatPassword).join(" · ")}</p> : <p className="unused-passwords-empty">Nenhuma senha em aberto hoje.</p>}{unused.length > unusedPreviewLimit && <Button type="button" variant="ghost" onClick={() => setUnusedOpen(true)}>Ver mais</Button>}</aside> : undefined} />
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
          <Field label="Atuação" htmlFor="activity" required><SearchableSelect id="activity" value={form.activity} onChange={(value) => update("activity", value)} options={activities.map((item) => ({ value: item, label: item }))} required /></Field>
          <Field label="CPF/CNPJ" htmlFor="cpf" hint="Zeros à esquerda serão preservados." required><input id="cpf" value={form.cpf_cnpj} onChange={(e) => update("cpf_cnpj", e.target.value)} inputMode="numeric" autoComplete="off" maxLength={18} required /></Field>
          <Field label="Plano atual" htmlFor="plan"><SearchableSelect id="plan" value={form.current_plan} onChange={(value) => update("current_plan", value)} options={plans.map((plan) => ({ value: plan, label: plan }))} /></Field>
          <Field label="Consultor" htmlFor="entry-consultant" required><SearchableSelect id="entry-consultant" value={form.consultant_id} onChange={(value) => update("consultant_id", value)} disabled={!store} options={consultants.map((item) => ({ value: String(item.id), label: item.name }))} required /></Field>
          <div className="span-full"><Field label="Classificação" htmlFor="classification-Disp Venda" required><div className="choice-board" role="radiogroup" aria-label="Classificação">{opportunityChoices.map((group) => <div className="choice-group" key={group.group}><strong>{group.group}</strong>{group.values.map((item) => <label className="choice-option" key={item} htmlFor={`classification-${item}`}><input id={`classification-${item}`} type="radio" name="classification" value={item} checked={(form.opportunity || form.non_opportunity) === item} onChange={() => selectClassification(item)} required />{item}</label>)}</div>)}</div></Field></div>
          <YesNoField label="Possui disponibilidade FTTH?" name="ftth" value={form.ftth_available} onChange={(value) => update("ftth_available", value)} />
          <YesNoField label="Disponível para venda?" name="available" value={form.available_for_sale} onChange={(value) => update("available_for_sale", value)} />
          <YesNoField label="Venda realizada?" name="sale" value={form.sale} onChange={(value) => { update("sale", value); update("reason_id", ""); update("order_number", ""); update("outcome_detail", ""); }} />
        </div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="form-actions">{editing && <Button type="button" variant="ghost" onClick={() => { setEditing(null); setForm(initialForm); }}>Cancelar edição</Button>}<Button type="submit" busy={busy} disabled={!store}><Plus size={18} /> {editing ? "Salvar alterações" : "Registrar atendimento"}</Button></div>
      </form>
    </div></Card>
    {unusedOpen && <div className="modal-layer" role="presentation"><div className="modal" role="dialog" aria-modal="true" aria-labelledby="unused-title"><div className="modal-header"><div><span className="eyebrow">Senhas do dia</span><h2 id="unused-title">Senhas não usadas</h2></div><button className="icon-button" type="button" onClick={() => setUnusedOpen(false)} aria-label="Fechar"><X size={20}/></button></div><div className="modal-body"><p>{unused.length} senha{unused.length === 1 ? "" : "s"} sem atendimento nesta loja.</p><div className="unused-password-grid" tabIndex={0}>{unused.map((item) => <span className="unused-password-chip" key={item}>{formatPassword(item)}</span>)}</div></div><div className="modal-footer"><Button type="button" variant="ghost" onClick={() => setUnusedOpen(false)}>Fechar</Button></div></div></div>}
    {finalizationOpen && <div className="modal-layer" role="presentation"><div className="modal" role="dialog" aria-modal="true" aria-labelledby="finalization-title"><div className="modal-header"><div><span className="eyebrow">Finalizar atendimento</span><h2 id="finalization-title">Venda {form.sale === "YES" ? "realizada" : "não realizada"}</h2></div><button className="icon-button" type="button" onClick={() => setFinalizationOpen(false)} aria-label="Fechar"><X size={20}/></button></div><form onSubmit={finalize}><div className="modal-body">{form.sale === "YES" && <Field label="Número da ordem" htmlFor="order-number" hint="Digite somente os números." required><input id="order-number" value={form.order_number} onChange={(event) => update("order_number", event.target.value.replace(/\D/g, ""))} inputMode="numeric" autoFocus required /></Field>}<Field label={form.sale === "YES" ? "Motivo da venda" : "Motivo da não venda"} htmlFor="reason" required><SearchableSelect id="reason" value={form.reason_id} onChange={(value) => update("reason_id", value)} options={visibleReasons.map((item) => ({ value: String(item.id), label: item.name }))} required /></Field><Field label="Classificação final" htmlFor="outcome-detail" required><SearchableSelect id="outcome-detail" value={form.outcome_detail} onChange={(value) => update("outcome_detail", value)} options={(form.sale === "YES" ? saleOutcomes : nonSaleOutcomes).map((item) => ({ value: item, label: item }))} required /></Field>{error && <p className="form-error" role="alert">{error}</p>}</div><div className="modal-footer"><Button type="button" variant="ghost" onClick={() => setFinalizationOpen(false)}>Voltar</Button><Button type="submit" busy={busy}>Finalizar atendimento</Button></div></form></div></div>}
    {notice && <div className="toast" role="status"><CheckCircle2 size={19} />{notice}</div>}
    <Card style={{ marginTop: 22 }}><div className="card-header"><div><h2>Atendimentos do dia</h2><p>{items.length} registro{items.length === 1 ? "" : "s"} na loja selecionada</p></div><div className="table-search"><Search size={17}/><input aria-label="Pesquisar atendimentos" placeholder="Senha, CPF/CNPJ ou consultor" value={search} onChange={(e) => setSearch(e.target.value)} /></div></div>
      {filtered.length ? <div className="table-wrap"><table><thead><tr><th>Senha</th><th>Atuação</th><th>CPF/CNPJ</th><th>Plano</th><th>Oportunidade</th><th>Não oportunidade</th><th>FTTH</th><th>Disp. venda</th><th>Venda</th><th>Ordem</th><th>Classificação final</th><th>Motivo</th><th>Consultor</th><th>Horário</th><th>Ações</th></tr></thead><tbody>{filtered.map((item) => <tr key={item.id}><td className="numeric"><strong>{item.password_number.toString().padStart(3,"0")}</strong></td><td>{item.activity || "—"}</td><td className="numeric">{item.cpf_cnpj}</td><td>{item.current_plan || "—"}</td><td>{item.opportunity || "—"}</td><td>{item.non_opportunity || "—"}</td><td><StatusBadge value={item.ftth_available}/></td><td><StatusBadge value={item.available_for_sale}/></td><td><StatusBadge value={item.sale}/></td><td className="numeric">{item.order_number || "—"}</td><td>{item.outcome_detail || "—"}</td><td>{item.reason_id ? reasonName[item.reason_id] : "—"}</td><td>{consultantName[item.consultant_id] ?? "—"}</td><td className="numeric">{new Date(item.created_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</td><td><div className="row-actions"><button onClick={() => edit(item)} aria-label={`Editar senha ${item.password_number}`}><Pencil size={16}/></button><button className="danger" onClick={() => remove(item)} aria-label={`Excluir senha ${item.password_number}`}><Trash2 size={16}/></button></div></td></tr>)}</tbody></table></div> : <EmptyState title={store ? "Nenhum atendimento encontrado" : "Selecione uma loja"} description={store ? "Registre o primeiro atendimento ou ajuste a pesquisa." : "Os atendimentos do dia aparecerão aqui."} />}
      {store && <div className="table-footer"><Button variant="ghost" onClick={loadDay}><RefreshCw size={16}/> Atualizar lista</Button></div>}
    </Card>
  </>;
}
