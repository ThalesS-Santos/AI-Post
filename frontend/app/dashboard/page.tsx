"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/Navbar";
import { PageLoader } from "@/components/ui/PageLoader";
import { GenerateButton } from "@/components/dashboard/GenerateButton";
import { PostCard } from "@/components/dashboard/PostCard";
import { SkeletonGrid } from "@/components/ui/SkeletonCard";
import { gerarPosts, getStatus, mensagemErro, type PostContent } from "@/lib/api";
import { useToast } from "@/lib/toast-context";
import { useRequireAuth } from "@/lib/use-require-auth";

const SUGESTOES = [
  "Promoção da semana",
  "Dia dos Namorados",
  "Novidade que chegou",
  "Fim de semana",
];

const QUANTIDADES = [
  { valor: 1, titulo: "1 post", sub: "Teste rápido", icon: "⚡" },
  { valor: 7, titulo: "7 posts", sub: "Uma semana", icon: "📅" },
  { valor: 30, titulo: "30 posts", sub: "Um mês inteiro", icon: "🗓️" },
];

const ESTILOS_IMAGEM = [
  "Realista", "3D Render", "Minimalista", "Cartoon", "Pixel Art",
  "Vintage", "Preto e Branco", "Cyberpunk", "Aquarela", "Óleo sobre Tela",
  "Neon", "Analógico", "Low Poly", "Flat", "Grunge"
];

export default function DashboardPage() {
  const { toast } = useToast();
  const router = useRouter();
  const { user, ready } = useRequireAuth();

  const [foco, setFoco] = useState("");
  const [quantidade, setQuantidade] = useState(7);
  const [loading, setLoading] = useState(false);
  const [posts, setPosts] = useState<PostContent[]>([]);
  const [checandoSetup, setChecandoSetup] = useState(true);
  const [estilosSelecionados, setEstilosSelecionados] = useState<string[]>([]);

  // Onboarding: só entra no painel quem já cadastrou marca + fotos.
  useEffect(() => {
    if (!ready || !user) return;
    getStatus(user.id)
      .then((s) => {
        if (!s.tem_marca || !s.tem_fotos) {
          router.replace("/setup");
        } else {
          setChecandoSetup(false);
        }
      })
      .catch(() => setChecandoSetup(false)); // se o status falhar, deixa entrar
  }, [ready, user, router]);

  if (!ready || !user || checandoSetup) return <PageLoader />;

  function toggleEstilo(estilo: string) {
    if (estilosSelecionados.includes(estilo)) {
      setEstilosSelecionados(estilosSelecionados.filter(e => e !== estilo));
    } else {
      if (estilosSelecionados.length >= 2) {
        toast("Você só pode escolher até 2 estilos simultaneamente.", "error");
        return;
      }
      setEstilosSelecionados([...estilosSelecionados, estilo]);
    }
  }

  async function handleGenerate() {
    if (quantidade === 1 && !foco.trim()) {
      toast("Escreva sobre o que você quer postar para gerar um post único.", "error");
      return;
    }
    setLoading(true);
    setPosts([]);
    try {
      const { posts: novos, gerados, solicitados } = await gerarPosts(
        user!.id,
        foco,
        quantidade,
        estilosSelecionados
      );
      setPosts(novos);
      if (gerados < solicitados) {
        toast(
          `Criamos ${gerados} de ${solicitados} posts. O restante parou no limite gratuito do Gemini — espere 1 min e gere mais.`,
          "info"
        );
      } else {
        toast(`Prontinho! ${gerados} posts criados.`, "success");
      }
    } catch (err: unknown) {
      toast(mensagemErro(err, "Não consegui criar os posts. Tente de novo."), "error");
    } finally {
      setLoading(false);
    }
  }

  function updatePost(index: number, novo: PostContent) {
    setPosts((prev) => prev.map((p, i) => (i === index ? novo : p)));
  }

  return (
    <>
      <Navbar cta={{ label: "+ Fotos", href: "/setup" }} />

      <main className="relative min-h-screen bg-surface-900 py-12 lg:py-16">
        <div
          className="pointer-events-none fixed inset-0"
          style={{
            background:
              "radial-gradient(ellipse 50% 30% at 70% 5%, rgba(124,58,237,0.1) 0%, transparent 70%)",
          }}
        />

        <div className="section-pad relative mx-auto max-w-9xl">
          {/* Caixa de criação */}
          <div className="glass-strong rounded-3xl p-7 lg:p-12">
            <h1 className="font-display text-[clamp(1.8rem,4vw,3.2rem)] font-extrabold leading-tight text-white">
              O que vamos postar hoje? ✨
            </h1>
            <p className="mt-3 text-[clamp(1rem,2vw,1.4rem)] text-white/55">
              Escreva o tema e escolha quantos posts quer criar com as suas fotos.
            </p>

            {/* Tema */}
            <div className="mt-8">
              <label htmlFor="tema" className="mb-2 block text-lg font-semibold text-white">
                1. Qual o tema? {quantidade > 1 && <span className="text-sm font-normal text-white/40">(Opcional)</span>}
              </label>
              <input
                id="tema"
                type="text"
                placeholder={quantidade > 1 ? "Deixe em branco para temas livres ou digite um foco geral" : "Ex: Promoção de Dia dos Namorados"}
                value={foco}
                onChange={(e) => setFoco(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                className="w-full rounded-2xl border border-white/10 bg-white/5 px-6 py-5 text-xl text-white placeholder-white/30 transition focus:border-brand-500 focus:outline-none"
              />
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <span className="text-base text-white/40">Ideias:</span>
                {SUGESTOES.map((s) => (
                  <button
                    key={s}
                    onClick={() => setFoco(s)}
                    className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-base text-white/70 transition-colors hover:border-brand-500 hover:text-white"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Quantidade */}
            <div className="mt-8">
              <label className="mb-3 block text-lg font-semibold text-white">
                2. Quantos posts?
              </label>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {QUANTIDADES.map((q) => (
                  <button
                    key={q.valor}
                    onClick={() => setQuantidade(q.valor)}
                    className={[
                      "flex items-center gap-4 rounded-2xl border-2 p-5 text-left transition-all",
                      quantidade === q.valor
                        ? "border-brand-500 bg-brand-900/30"
                        : "border-white/10 bg-white/5 hover:border-white/25",
                    ].join(" ")}
                  >
                    <span className="text-4xl">{q.icon}</span>
                    <span>
                      <span className="block text-xl font-bold text-white">
                        {q.titulo}
                      </span>
                      <span className="block text-base text-white/50">{q.sub}</span>
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Estilos */}
            <div className="mt-8">
              <label className="mb-3 block text-lg font-semibold text-white">
                3. Estilo Visual <span className="text-sm font-normal text-white/40">(Opcional, escolha até 2)</span>
              </label>
              <div className="flex flex-wrap items-center gap-2">
                {ESTILOS_IMAGEM.map((estilo) => {
                  const isSelected = estilosSelecionados.includes(estilo);
                  return (
                    <button
                      key={estilo}
                      onClick={() => toggleEstilo(estilo)}
                      className={[
                        "rounded-full border px-4 py-2 text-base transition-colors",
                        isSelected
                          ? "border-brand-500 bg-brand-600 text-white"
                          : "border-white/10 bg-white/5 text-white/70 hover:border-brand-500 hover:text-white"
                      ].join(" ")}
                    >
                      {estilo}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Botão gerar */}
            <div className="mt-8">
              <GenerateButton onClick={handleGenerate} loading={loading} />
            </div>
          </div>

          {/* Carregando */}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-12"
            >
              <p className="mb-6 text-center text-xl text-white/55">
                ⏳ Criando seus posts… isso pode levar alguns minutos para lotes
                grandes.
              </p>
              <SkeletonGrid count={Math.min(quantidade, 6)} />
            </motion.div>
          )}

          {/* Resultado */}
          <AnimatePresence>
            {posts.length > 0 && !loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-12"
              >
                <h2 className="mb-6 font-display text-2xl font-bold text-white lg:text-3xl">
                  Seus {posts.length} posts estão prontos 🎉
                </h2>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3 3xl:grid-cols-4">
                  {posts.map((post, i) => (
                    <PostCard
                      key={i}
                      post={post}
                      index={i}
                      foco={foco}
                      clienteId={user.id}
                      onUpdate={updatePost}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Vazio */}
          {!loading && posts.length === 0 && (
            <div className="mt-16 flex flex-col items-center gap-4 py-16 text-center">
              <span className="text-7xl opacity-30">📝</span>
              <p className="text-xl text-white/40">
                Seus posts vão aparecer aqui assim que você criar.
              </p>
            </div>
          )}
        </div>
      </main>
    </>
  );
}
