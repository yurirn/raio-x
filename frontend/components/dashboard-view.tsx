"use client";

import { Activity, ArrowDown, ArrowUp, ArrowUpDown, CalendarDays, Download, RadioTower, ShoppingBag, TicketCheck, TrendingUp, Users } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, download } from "@/lib/api";
import type { DashboardData, NamedEntity } from "@/lib/types";
import { Button, Card, EmptyState, Field, PageHeader, SearchableSelect, Skeleton } from "./ui";

const today = new Date().toISOString().slice(0, 10);
const firstDay = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().slice(0, 10);
const colors = ["#0f766e", "#0891b2", "#2563eb", "#7c3aed", "#b45309", "#64748b"];
const brDate = (value: string) => value.split("-").reverse().join("/");
const currentPlans = ["Pre Pago", "Controle ate R$60,00", "Controle acima R$60,00", "Vivo Total", "Pos pago", "Fibra avulsa", "Outras Operadoras"];

function Metric({ label, value, icon: Icon }: { label: string; value: string | number; icon: typeof Activity }) {
  return <Card className="metric-card"><span className="metric-icon"><Icon size={19} /></span><span className="metric-label">{label}</span><strong className="metric-value">{value}</strong></Card>;
}

type SortKey = "passwords" | "ftth_available" | "available_for_sale" | "sales" | "share_passwords" | "availability_percentage" | "availability_real_percentage" | "conversion";
type TableRow = Record<SortKey, number> & { id: number; name: string };
const columns: Array<{ key: SortKey; label: string; suffix?: string }> = [
  { key: "passwords", label: "Senhas" }, { key: "ftth_available", label: "FTTH" }, { key: "available_for_sale", label: "Disp. venda" }, { key: "sales", label: "Vendas" }, { key: "share_passwords", label: "Participação", suffix: "%" }, { key: "availability_percentage", label: "Disponibilidade", suffix: "%" }, { key: "availability_real_percentage", label: "Disp. real", suffix: "%" }, { key: "conversion", label: "Conversão", suffix: "%" },
];

function PerformanceTable({ title, description, entity, rows }: { title: string; description: string; entity: string; rows: TableRow[] }) {
  const [sort, setSort] = useState<{ key: SortKey; direction: "asc" | "desc" }>({ key: "sales", direction: "desc" });
  const sortedRows = useMemo(() => [...rows].sort((a, b) => sort.direction === "desc" ? b[sort.key] - a[sort.key] : a[sort.key] - b[sort.key]), [rows, sort]);
  function changeSort(key: SortKey) { setSort((current) => ({ key, direction: current.key === key && current.direction === "desc" ? "asc" : "desc" })); }
  return <Card style={{ marginTop: 20 }}><div className="card-header"><div><h2>{title}</h2><p>{description}</p></div></div><div className="table-wrap"><table><thead><tr><th>{entity}</th>{columns.map((column) => <th key={column.key}><button className="table-sort" onClick={() => changeSort(column.key)} aria-sort={sort.key === column.key ? (sort.direction === "desc" ? "descending" : "ascending") : "none"}>{column.label}{sort.key === column.key ? sort.direction === "desc" ? <ArrowDown size={15} /> : <ArrowUp size={15} /> : <ArrowUpDown size={14} />}</button></th>)}</tr></thead><tbody>{sortedRows.map((item) => <tr key={item.id}><td><strong>{item.name}</strong></td>{columns.map((column) => <td className="numeric" key={column.key}>{column.key === "conversion" ? <strong>{item[column.key]}{column.suffix}</strong> : <>{item[column.key]}{column.suffix}</>}</td>)}</tr>)}</tbody></table></div></Card>;
}

export function DashboardView({ overview = false }: { overview?: boolean }) {
  const [start, setStart] = useState(overview ? today : firstDay);
  const [end, setEnd] = useState(today);
  const [regional, setRegional] = useState("");
  const [coordinator, setCoordinator] = useState("");
  const [store, setStore] = useState("");
  const [consultant, setConsultant] = useState("");
  const [currentPlan, setCurrentPlan] = useState("");
  const [regionals, setRegionals] = useState<NamedEntity[]>([]);
  const [coordinators, setCoordinators] = useState<NamedEntity[]>([]);
  const [stores, setStores] = useState<NamedEntity[]>([]);
  const [consultants, setConsultants] = useState<NamedEntity[]>([]);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { api<NamedEntity[]>("/catalog/regionals").then(setRegionals); }, []);
  useEffect(() => { setCoordinator(""); setStore(""); setConsultant(""); api<NamedEntity[]>(`/catalog/coordinators${regional ? `?regional_id=${regional}` : ""}`).then(setCoordinators); }, [regional]);
  useEffect(() => { setStore(""); setConsultant(""); api<NamedEntity[]>(`/catalog/stores${coordinator ? `?coordinator_id=${coordinator}` : ""}`).then(setStores); }, [coordinator]);
  useEffect(() => { setConsultant(""); if (store) api<NamedEntity[]>(`/catalog/consultants?store_id=${store}`).then(setConsultants); else setConsultants([]); }, [store]);

  const query = useMemo(() => {
    const params = new URLSearchParams({ start_date: start, end_date: end });
    if (regional) params.set("regional_id", regional); if (coordinator) params.set("coordinator_id", coordinator);
    if (store) params.set("store_id", store); if (consultant) params.set("consultant_id", consultant);
    if (currentPlan) params.set("current_plan", currentPlan);
    return params.toString();
  }, [start, end, regional, coordinator, store, consultant, currentPlan]);
  const load = useCallback(async () => { setLoading(true); setError(""); try { setData(await api<DashboardData>(`/dashboard/consolidated?${query}`)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao carregar."); } finally { setLoading(false); } }, [query]);
  useEffect(() => { load(); }, [load]);

  const cards = data?.cards;
  return <>
    <PageHeader eyebrow={overview ? "Visão de hoje" : "Inteligência de desempenho"} title={overview ? "Dashboard operacional" : "Consolidado"} description={overview ? "Acompanhe o ritmo da operação e os principais resultados do dia." : "Compare resultados, identifique oportunidades e exporte o recorte selecionado."} action={<div className="button-row"><Button variant="secondary" onClick={() => download(`/exports/consolidated.xlsx?${query}`, "consolidado.xlsx")}><Download size={17} /> Exportar Excel</Button></div>} />
    {!overview && <Card className="filters" aria-label="Filtros do consolidado">
      <Field label="Data inicial" htmlFor="start"><input id="start" type="date" value={start} onChange={(e) => setStart(e.target.value)} /></Field>
      <Field label="Data final" htmlFor="end"><input id="end" type="date" value={end} onChange={(e) => setEnd(e.target.value)} /></Field>
      <Field label="Regional" htmlFor="regional"><SearchableSelect id="regional" value={regional} onChange={setRegional} placeholder="Todas" options={regionals.map((item) => ({ value: String(item.id), label: item.name }))} /></Field>
      <Field label="Coordenador" htmlFor="coordinator"><SearchableSelect id="coordinator" value={coordinator} onChange={setCoordinator} placeholder="Todos" options={coordinators.map((item) => ({ value: String(item.id), label: item.name }))} /></Field>
      <Field label="Loja" htmlFor="store"><SearchableSelect id="store" value={store} onChange={setStore} placeholder="Todas" options={stores.map((item) => ({ value: String(item.id), label: item.name }))} /></Field>
      <Field label="Consultor" htmlFor="consultant"><SearchableSelect id="consultant" value={consultant} onChange={setConsultant} disabled={!store} placeholder="Todos" options={consultants.map((item) => ({ value: String(item.id), label: item.name }))} /></Field>
      <Field label="Plano atual" htmlFor="current-plan"><SearchableSelect id="current-plan" value={currentPlan} onChange={setCurrentPlan} placeholder="Todos" options={currentPlans.map((item) => ({ value: item, label: item }))} /></Field>
    </Card>}
    {error && <p className="form-error" role="alert">{error} <button onClick={load}>Tentar novamente</button></p>}
    {loading ? <div className="metrics-grid">{Array.from({ length: 6 }, (_, index) => <Skeleton key={index} height={126} />)}</div> : <div className="metrics-grid">
      <Metric label="Total de senhas" value={cards?.passwords ?? 0} icon={TicketCheck} /><Metric label="Com disponibilidade" value={cards?.ftth_available ?? 0} icon={RadioTower} /><Metric label="Disponível para venda" value={cards?.available_for_sale ?? 0} icon={ShoppingBag} /><Metric label="Vendas" value={cards?.sales ?? 0} icon={TrendingUp} /><Metric label="Conversão" value={`${(cards?.conversion ?? 0).toLocaleString("pt-BR")}%`} icon={Activity} /><Metric label="Consultores ativos" value={cards?.active_consultants ?? 0} icon={Users} />
    </div>}
    <div className="content-grid">
      <Card><div className="card-header"><div><h2>Movimento diário</h2><p>Senhas registradas por dia</p></div><CalendarDays size={19} color="#64748b" /></div><div className="chart-wrap">{data?.daily.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.daily}><CartesianGrid stroke="#e8edf1" vertical={false}/><XAxis dataKey="date" tickFormatter={brDate} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false}/><YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} axisLine={false} tickLine={false}/><Tooltip labelFormatter={(value) => brDate(String(value))}/><Bar dataKey="passwords" name="Senhas" fill="#0f766e" radius={[6, 6, 0, 0]}/></BarChart></ResponsiveContainer> : <EmptyState title="Sem movimento no período" description="Os dados aparecerão aqui após o primeiro atendimento." />}</div></Card>
      <Card><div className="card-header"><div><h2>Ranking de vendas</h2><p>Consultores com melhor resultado</p></div></div><div className="card-body">{data?.ranking.length ? data.ranking.slice(0, 6).map((item) => <div className="rank" key={item.consultant_id}><span className="rank-number">{item.position}</span><div><strong>{item.consultant}</strong><small>{item.conversion.toLocaleString("pt-BR")}% conversão</small></div><span className="rank-value">{item.sales}</span></div>) : <EmptyState title="Ranking indisponível" description="Ainda não existem vendas para este filtro." />}</div></Card>
    </div>
    {!overview && <><div className="chart-grid"><Card><div className="card-header"><div><h2>Vendas por consultor</h2><p>Comparação do período</p></div></div><div className="chart-wrap">{data?.performance.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.performance.slice(0, 10)} layout="vertical" margin={{ left: 20 }}><CartesianGrid stroke="#e8edf1" horizontal={false}/><XAxis type="number" allowDecimals={false} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="consultant" width={90} axisLine={false} tickLine={false} tick={{ fontSize: 12 }}/><Tooltip/><Bar dataKey="sales" name="Vendas" fill="#0f766e" radius={[0, 6, 6, 0]}/></BarChart></ResponsiveContainer> : <EmptyState title="Sem dados" description="Ajuste o filtro ou registre atendimentos." />}</div></Card><Card><div className="card-header"><div><h2>Motivos de não venda</h2><p>Principais obstáculos no período</p></div></div><div className="chart-wrap">{data?.reasons.length ? <ResponsiveContainer width="100%" height="100%"><BarChart data={data.reasons.slice(0, 8)}><CartesianGrid stroke="#e8edf1" vertical={false}/><XAxis dataKey="reason" tick={{ fontSize: 11 }} axisLine={false} tickLine={false}/><YAxis allowDecimals={false} axisLine={false} tickLine={false}/><Tooltip/><Bar dataKey="count" name="Ocorrências" radius={[6,6,0,0]}>{data.reasons.slice(0,8).map((_, index) => <Cell key={index} fill={colors[index % colors.length]}/>)}</Bar></BarChart></ResponsiveContainer> : <EmptyState title="Sem motivos registrados" description="Não há recusas no período selecionado." />}</div></Card></div>
      <PerformanceTable title="Desempenho por consultor" description="Indicadores calculados a partir dos atendimentos" entity="Consultor" rows={(data?.performance ?? []).map((item) => ({ ...item, id: item.consultant_id, name: item.consultant }))} />
      <PerformanceTable title="Desempenho por loja" description="Resultados consolidados por unidade no período selecionado" entity="Loja" rows={(data?.store_performance ?? []).map((item) => ({ ...item, id: item.store_id, name: item.store }))} /></>}
  </>;
}
