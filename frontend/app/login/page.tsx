"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/Navbar";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/lib/toast-context";

export default function LoginPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user, loading, signIn, signUp } = useAuth();

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  // Já logado? vai direto para o painel.
  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !password) {
      toast("Preencha e-mail e senha.", "error");
      return;
    }
    setBusy(true);
    try {
      if (mode === "login") {
        await signIn(email, password);
        toast("Bem-vindo de volta! 👋", "success");
        router.replace("/dashboard");
      } else {
        const { needsConfirm } = await signUp(email, password);
        if (needsConfirm) {
          toast(
            "Conta criada! Confirme pelo link enviado no seu e-mail para entrar.",
            "info"
          );
          setMode("login");
        } else {
          toast("Conta criada com sucesso! 🎉", "success");
          router.replace("/setup");
        }
      }
    } catch (err: unknown) {
      toast(err instanceof Error ? err.message : "Algo deu errado.", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Navbar />
      <main className="relative flex min-h-[calc(100vh-5rem)] items-center justify-center bg-surface-900 py-12">
        <div
          className="pointer-events-none fixed inset-0"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 50% 30%, rgba(124,58,237,0.14) 0%, transparent 70%)",
          }}
        />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 90, damping: 16 }}
          className="section-pad relative w-full max-w-lg"
        >
          <div className="glass-strong rounded-3xl p-8 lg:p-10">
            {/* Abas */}
            <div className="mb-8 flex rounded-2xl bg-white/5 p-1.5">
              {(["login", "signup"] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={[
                    "flex-1 rounded-xl py-3 text-lg font-bold transition-colors",
                    mode === m
                      ? "bg-brand-600 text-white"
                      : "text-white/50 hover:text-white",
                  ].join(" ")}
                >
                  {m === "login" ? "Entrar" : "Criar conta"}
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={mode}
                initial={{ opacity: 0, x: mode === "login" ? -15 : 15 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                <h1 className="font-display text-3xl font-extrabold text-white">
                  {mode === "login" ? "Que bom te ver! 👋" : "Vamos começar! 🚀"}
                </h1>
                <p className="mt-2 text-lg text-white/55">
                  {mode === "login"
                    ? "Entre para ver suas fotos e criar posts."
                    : "Crie sua conta. Suas fotos ficam salvas para sempre."}
                </p>
              </motion.div>
            </AnimatePresence>

            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              <div className="space-y-2">
                <label htmlFor="email" className="block text-lg font-semibold text-white">
                  Seu e-mail
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="voce@exemplo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-white placeholder-white/30 transition focus:border-brand-500 focus:outline-none"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-lg font-semibold text-white">
                  Sua senha
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  placeholder="Pelo menos 6 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-white placeholder-white/30 transition focus:border-brand-500 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={busy}
                className="glow-purple-sm flex w-full items-center justify-center gap-2 rounded-2xl bg-brand-600 py-5 text-xl font-bold text-white transition-all hover:scale-[1.01] hover:bg-brand-500 disabled:scale-100 disabled:opacity-60"
              >
                {busy
                  ? "Aguarde…"
                  : mode === "login"
                    ? "Entrar →"
                    : "Criar minha conta →"}
              </button>
            </form>
          </div>
        </motion.div>
      </main>
    </>
  );
}
