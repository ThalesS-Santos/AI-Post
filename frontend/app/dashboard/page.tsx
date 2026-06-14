"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Navbar } from "@/components/ui/Navbar";
import { GenerateButton } from "@/components/dashboard/GenerateButton";
import { SkeletonGrid } from "@/components/ui/SkeletonCard";
import { gerarPosts, type PostContent } from "@/lib/api";
import { useToast } from "@/lib/toast-context";

const DEMO_CLIENT_ID = "00000000-0000-0000-0000-000000000001";

const SUGESTOES = [
  "Promoção da semana",
  "Dia dos Namorados",
  "Novidade que chegou",
  "Fim de semana",
];

export default function DashboardPage() {
  const { toast } = useToast();
  const [foco, setFoco] = useState("");
  const [loading, setLoading] = useState(false);
  const [posts, setPosts] = useState<PostContent[]>([]);

  async function handleGenerate() {
    if (!foco.trim()) {
      toast("Escreva sobre o que você quer postar.", "error");
      return;
    }
    setLoading(true);
    setPosts([]);
    try {
      const result = await gerarPosts(DEMO_CLIENT_ID, foco, 7);
      setPosts(result);
      toast(`Prontinho! ${result.length} posts criados.`, "success");
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Não consegui criar os posts. Tente de novo.";
      toast(msg, "error");
    } finally {
      setLoading(false);
    }
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
              Escreva o tema da semana. A gente cria 7 posts prontos com as suas
              fotos.
            </p>

            <div className="mt-8 flex flex-col gap-4 lg:flex-row">
              <input
                type="text"
                placeholder="Ex: Promoção de Dia dos Namorados"
                value={foco}
                onChange={(e) => setFoco(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-6 py-5 text-xl text-white placeholder-white/30 transition focus:border-brand-500 focus:outline-none"
              />
              <GenerateButton onClick={handleGenerate} loading={loading} />
            </div>

            {/* Sugestões rápidas */}
            <div className="mt-5 flex flex-wrap items-center gap-3">
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

          {/* Carregando */}
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-12"
            >
              <p className="mb-6 text-center text-xl text-white/55">
                ⏳ Criando seus posts… isso leva alguns segundinhos.
              </p>
              <SkeletonGrid count={6} />
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
                    <PostCard key={i} post={post} index={i} />
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

function PostCard({ post, index }: { post: PostContent; index: number }) {
  const [copied, setCopied] = useState(false);

  function copyLegenda() {
    navigator.clipboard.writeText(
      `${post.legenda_instagram}\n\n${post.hashtags.map((h) => `#${h}`).join(" ")}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "spring",
        stiffness: 80,
        damping: 16,
        delay: index * 0.06,
      }}
      className="glass flex h-full flex-col gap-5 rounded-3xl p-7"
    >
      {/* Cabeçalho */}
      <div className="flex items-start justify-between gap-3">
        <h3 className="flex-1 text-xl font-bold leading-snug text-white">
          {post.titulo_interno}
        </h3>
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand-900/40 text-base font-bold text-brand-300">
          {index + 1}
        </span>
      </div>

      {/* Legenda */}
      <p className="flex-1 text-lg leading-relaxed text-white/70">
        {post.legenda_instagram}
      </p>

      {/* Dica visual */}
      <div className="rounded-2xl border border-brand-700/30 bg-brand-900/25 px-4 py-3">
        <p className="text-base text-brand-200">
          <span className="font-semibold">🎨 Dica de foto: </span>
          {post.sugestao_de_edicao_visual}
        </p>
      </div>

      {/* Hashtags */}
      <div className="flex flex-wrap gap-2">
        {post.hashtags.map((h) => (
          <span
            key={h}
            className="rounded-full bg-brand-900/30 px-3 py-1 text-base font-medium text-brand-300"
          >
            #{h}
          </span>
        ))}
      </div>

      {/* Botão copiar */}
      <button
        onClick={copyLegenda}
        className={[
          "mt-auto w-full rounded-2xl py-4 text-lg font-bold transition-all",
          copied
            ? "bg-green-600/80 text-white"
            : "bg-brand-600 text-white hover:bg-brand-500",
        ].join(" ")}
      >
        {copied ? "✓ Copiado!" : "📋 Copiar para o Instagram"}
      </button>
    </motion.div>
  );
}
