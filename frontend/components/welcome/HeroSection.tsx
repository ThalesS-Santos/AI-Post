"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "framer-motion";

const ParticleMesh = dynamic(
  () => import("@/components/three/ParticleMesh").then((m) => m.ParticleMesh),
  { ssr: false }
);

const spring = { type: "spring" as const, stiffness: 100, damping: 14 };

export function HeroSection() {
  return (
    <section className="relative flex min-h-[calc(100vh-5rem)] items-center overflow-hidden bg-surface-900">
      {/* Brilho radial de fundo */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 90% 70% at 50% 35%, rgba(124,58,237,0.16) 0%, transparent 70%)",
        }}
      />

      {/* Malha 3D de partículas */}
      <ParticleMesh />

      <div className="section-pad relative z-10 mx-auto grid w-full max-w-9xl items-center gap-12 py-16 lg:grid-cols-2 lg:gap-8 lg:py-24">
        {/* Coluna de texto */}
        <div className="text-center lg:text-left">
          <motion.span
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.05 }}
            className="inline-flex items-center gap-2 rounded-full border border-brand-700/40 bg-brand-900/30 px-5 py-2 text-sm font-semibold uppercase tracking-widest text-brand-300 md:text-base"
          >
            🚀 Feito para o seu negócio
          </motion.span>

          <motion.h1
            initial={{ opacity: 0, y: 60 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.15 }}
            className="mt-6 font-display text-[clamp(2.5rem,7vw,5.5rem)] font-extrabold leading-[1.05] tracking-tight text-white"
          >
            Posts prontos
            <br />
            para vender,
            <br />
            <span className="text-gradient">em segundos.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.3 }}
            className="mx-auto mt-7 max-w-2xl text-[clamp(1.1rem,2.2vw,1.6rem)] leading-relaxed text-white/65 lg:mx-0"
          >
            Você manda a foto do seu produto. A gente escreve a legenda, o título
            e as hashtags. Simples assim — sem precisar entender nada de
            tecnologia.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ ...spring, delay: 0.45 }}
            className="mt-10 flex flex-col items-stretch gap-4 sm:flex-row sm:items-center lg:justify-start"
          >
            <Link
              href="/setup"
              className="glow-purple-sm inline-flex items-center justify-center gap-2 rounded-2xl bg-brand-600 px-9 py-5 text-xl font-bold text-white transition-all hover:scale-[1.03] hover:bg-brand-500"
            >
              Começar agora — é grátis
            </Link>
            <a
              href="#como-funciona"
              className="inline-flex items-center justify-center gap-2 rounded-2xl border-2 border-white/15 px-9 py-5 text-xl font-bold text-white/80 transition-colors hover:border-white/30 hover:text-white"
            >
              Ver como funciona
            </a>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9 }}
            className="mt-6 text-base text-white/40"
          >
            ✓ Sem cartão de crédito &nbsp;·&nbsp; ✓ Pronto em 2 minutos
          </motion.p>
        </div>

        {/* Coluna visual: mockup de exemplo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ ...spring, delay: 0.4 }}
          className="hidden lg:block"
        >
          <ExampleCard />
        </motion.div>
      </div>

      {/* Indicador de scroll */}
      <motion.a
        href="#como-funciona"
        className="absolute bottom-8 left-1/2 z-10 flex -translate-x-1/2 flex-col items-center gap-2 text-base text-white/40"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2 }}
      >
        <span>role para baixo</span>
        <motion.span
          animate={{ y: [0, 8, 0] }}
          transition={{ repeat: Infinity, duration: 1.6, ease: "easeInOut" }}
          className="text-2xl"
        >
          ↓
        </motion.span>
      </motion.a>
    </section>
  );
}

/** Cartão de exemplo mostrando o resultado real do produto. */
function ExampleCard() {
  return (
    <div className="glass-strong mx-auto max-w-md rounded-3xl p-7 shadow-2xl 3xl:max-w-lg">
      <div className="flex items-center gap-3 border-b border-white/10 pb-4">
        <div className="grid h-12 w-12 place-items-center rounded-full bg-gradient-to-br from-brand-400 to-brand-700 text-2xl">
          🧁
        </div>
        <div>
          <p className="text-lg font-bold text-white">Bolos da Vovó</p>
          <p className="text-sm text-white/45">agora mesmo</p>
        </div>
      </div>

      <div className="flex aspect-square items-center justify-center bg-gradient-to-br from-brand-900/40 to-surface-700 text-7xl">
        🎂
      </div>

      <div className="pt-4">
        <p className="text-lg leading-relaxed text-white/85">
          No Dia dos Namorados, adoce a vida de quem você ama com um bolo feito
          com carinho. ❤️
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {["#BolosDaVovo", "#FeitoComAmor", "#DiaDosNamorados"].map((h) => (
            <span
              key={h}
              className="rounded-full bg-brand-900/40 px-3 py-1 text-sm font-medium text-brand-300"
            >
              {h}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
