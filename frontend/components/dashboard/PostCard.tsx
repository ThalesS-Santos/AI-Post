"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  regenerarImagem,
  regenerarLegenda,
  mensagemErro,
  type PostContent,
} from "@/lib/api";
import { useToast } from "@/lib/toast-context";

type Acao = "legenda" | "imagem" | "tudo" | null;

interface PostCardProps {
  post: PostContent;
  index: number;
  foco: string;
  clienteId: string;
  onUpdate: (index: number, novo: PostContent) => void;
}

export function PostCard({ post, index, foco, clienteId, onUpdate }: PostCardProps) {
  const { toast } = useToast();
  const [busy, setBusy] = useState<Acao>(null);
  const [copied, setCopied] = useState(false);

  const [carouselIndex, setCarouselIndex] = useState(0);

  const isCarousel = post.imagens_carrossel_base64 && post.imagens_carrossel_base64.length > 0;
  const currentImageB64 = isCarousel 
    ? post.imagens_carrossel_base64![carouselIndex] 
    : post.imagem_gerada_base64;

  const temIA = post.imagem_disponivel && !!currentImageB64;
  const imgSrc = temIA
    ? `data:image/png;base64,${currentImageB64}`
    : post.produto_url || null;

  function copyLegenda() {
    navigator.clipboard.writeText(
      `${post.legenda_instagram}\n\n${post.hashtags.map((h) => `#${h}`).join(" ")}`
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function refazerLegenda() {
    if (!post.produto_id) return;
    setBusy("legenda");
    try {
      const novo = await regenerarLegenda(clienteId, foco, post.produto_id);
      // Mantém a imagem atual, troca só o texto.
      onUpdate(index, {
        ...novo,
        imagem_gerada_base64: post.imagem_gerada_base64,
        imagem_disponivel: post.imagem_disponivel,
      });
      toast("Legenda refeita! ✍️", "success");
    } catch (err) {
      toast(mensagemErro(err, "Não consegui refazer a legenda."), "error");
    } finally {
      setBusy(null);
    }
  }

  async function refazerImagem() {
    if (!post.produto_id) return;
    setBusy("imagem");
    try {
      const r = await regenerarImagem(
        clienteId,
        foco,
        post.produto_id,
        post.legenda_instagram
      );
      if (!r.imagem_disponivel) {
        toast(
          "A geração de imagem por IA requer plano pago no Gemini. Por enquanto, usamos a sua foto original.",
          "info"
        );
      } else {
        toast("Imagem refeita! 🖼️", "success");
      }
      onUpdate(index, {
        ...post,
        imagem_gerada_base64: r.imagem_gerada_base64,
        imagem_disponivel: r.imagem_disponivel,
      });
    } catch (err) {
      toast(mensagemErro(err, "Não consegui refazer a imagem."), "error");
    } finally {
      setBusy(null);
    }
  }

  async function refazerTudo() {
    if (!post.produto_id) return;
    setBusy("tudo");
    try {
      // 1) nova legenda
      const novo = await regenerarLegenda(clienteId, foco, post.produto_id);
      // 2) nova imagem a partir da nova legenda
      const r = await regenerarImagem(
        clienteId,
        foco,
        post.produto_id,
        novo.legenda_instagram
      );
      onUpdate(index, {
        ...novo,
        imagem_gerada_base64: r.imagem_gerada_base64,
        imagem_disponivel: r.imagem_disponivel,
      });
      toast("Post refeito do zero! ♻️", "success");
    } catch (err) {
      toast(mensagemErro(err, "Não consegui refazer o post."), "error");
    } finally {
      setBusy(null);
    }
  }

  const anyBusy = busy !== null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 80, damping: 16, delay: index * 0.05 }}
      className="glass flex h-full flex-col gap-4 rounded-3xl p-6"
    >
      {/* Imagem */}
      {imgSrc && (
        <div className="relative overflow-hidden rounded-2xl">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={imgSrc}
            alt={post.titulo_interno}
            className={
              post.titulo_interno.toLowerCase().includes("storie")
                ? "aspect-[9/16] w-full object-cover"
                : "aspect-square w-full object-cover"
            }
          />
          <span
            className={[
              "absolute left-3 top-3 rounded-full px-3 py-1 text-sm font-semibold backdrop-blur",
              temIA
                ? "bg-brand-600/80 text-white"
                : "bg-black/60 text-white/90",
            ].join(" ")}
          >
            {temIA ? "✨ Imagem por IA" : "📷 Sua foto"}
          </span>

          {/* Carousel Controls */}
          {isCarousel && post.imagens_carrossel_base64!.length > 1 && (
            <>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setCarouselIndex((prev) => (prev > 0 ? prev - 1 : post.imagens_carrossel_base64!.length - 1));
                }}
                className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-black/60 p-2 text-base text-white hover:bg-black/85 transition-colors"
                title="Imagem anterior"
              >
                ◀
              </button>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setCarouselIndex((prev) => (prev < post.imagens_carrossel_base64!.length - 1 ? prev + 1 : 0));
                }}
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-black/60 p-2 text-base text-white hover:bg-black/85 transition-colors"
                title="Próxima imagem"
              >
                ▶
              </button>
              <span className="absolute bottom-3 right-3 rounded-lg bg-black/70 px-2.5 py-1 text-xs font-bold text-white backdrop-blur-sm">
                {carouselIndex + 1} / {post.imagens_carrossel_base64!.length}
              </span>
            </>
          )}

          {busy === "imagem" || busy === "tudo" ? (
            <div className="absolute inset-0 grid place-items-center bg-black/60 text-lg font-semibold text-white">
              Refazendo imagem…
            </div>
          ) : null}
        </div>
      )}

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
        {busy === "legenda" || busy === "tudo" ? (
          <span className="text-white/40">Reescrevendo legenda…</span>
        ) : (
          post.legenda_instagram
        )}
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

      {/* Refazer — só o que o usuário não gostou */}
      <div className="grid grid-cols-3 gap-2">
        <RefazerBtn
          label="Legenda"
          icon="✍️"
          active={busy === "legenda"}
          disabled={anyBusy}
          onClick={refazerLegenda}
        />
        <RefazerBtn
          label="Imagem"
          icon="🖼️"
          active={busy === "imagem"}
          disabled={anyBusy}
          onClick={refazerImagem}
        />
        <RefazerBtn
          label="Tudo"
          icon="♻️"
          active={busy === "tudo"}
          disabled={anyBusy}
          onClick={refazerTudo}
        />
      </div>

      {/* Copiar */}
      <button
        onClick={copyLegenda}
        disabled={anyBusy}
        className={[
          "mt-auto w-full rounded-2xl py-4 text-lg font-bold transition-all disabled:opacity-50",
          copied ? "bg-green-600/80 text-white" : "bg-brand-600 text-white hover:bg-brand-500",
        ].join(" ")}
      >
        {copied ? "✓ Copiado!" : "📋 Copiar para o Instagram"}
      </button>
    </motion.div>
  );
}

function RefazerBtn({
  label,
  icon,
  active,
  disabled,
  onClick,
}: {
  label: string;
  icon: string;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={`Refazer ${label.toLowerCase()}`}
      className={[
        "flex flex-col items-center gap-1 rounded-xl border py-3 text-sm font-semibold transition-colors disabled:opacity-40",
        active
          ? "border-brand-500 bg-brand-900/40 text-white"
          : "border-white/10 bg-white/5 text-white/70 hover:border-brand-500 hover:text-white",
      ].join(" ")}
    >
      <span className="text-xl">{active ? "⏳" : icon}</span>
      {label}
    </button>
  );
}
