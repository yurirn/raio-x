"use client";

import Image from "next/image";
import { Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { Button, Field } from "@/components/ui";
import { api, getToken, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@raiox.local");
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { if (getToken()) router.replace("/dashboard"); }, [router]);
  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const result = await api<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setToken(result.access_token); router.replace("/dashboard");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao entrar."); }
    finally { setBusy(false); }
  }
  return <main className="login-page">
    <section className="login-panel" aria-labelledby="login-title">
      <div className="login-brand">
        <Image src="/logo-vivo.webp" alt="Vivo" width={128} height={40} priority />
        <span aria-hidden="true" />
        <strong>Raio X</strong>
      </div>
      <div className="login-copy">
        <span className="login-kicker">Portal operacional</span>
        <h1 id="login-title">Acesse sua conta</h1>
        <p>Entre para acompanhar os indicadores e registrar os resultados da sua operação.</p>
      </div>
      <form className="login-form" onSubmit={submit}>
        <Field label="E-mail" htmlFor="email" required><div className="input-with-icon"><Mail size={18} /><input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required /></div></Field>
        <Field label="Senha" htmlFor="password" required><div className="input-with-icon"><LockKeyhole size={18} /><input id="password" type={visible ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" minLength={8} required /><button type="button" onClick={() => setVisible(!visible)} aria-label={visible ? "Ocultar senha" : "Mostrar senha"}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></Field>
        {error && <p className="form-error" role="alert">{error}</p>}
        <Button type="submit" busy={busy}>Entrar</Button>
      </form>
      <p className="login-help">Acesso exclusivo para colaboradores autorizados.</p>
    </section>
    <aside className="login-visual" aria-label="Apresentação do sistema Raio X">
      <div className="visual-orb visual-orb-one" aria-hidden="true" />
      <div className="visual-orb visual-orb-two" aria-hidden="true" />
      <div className="visual-content">
        <span className="login-kicker">Raio X</span>
        <h2>Clareza para cada decisão da operação.</h2>
        <p>Uma visão única dos atendimentos, oportunidades e resultados da sua equipe.</p>
        <div className="visual-stats"><div><strong>01</strong><span>base integrada</span></div><div><strong>100%</strong><span>rastreável</span></div><div><strong>Ao vivo</strong><span>indicadores</span></div></div>
      </div>
    </aside>
  </main>;
}
