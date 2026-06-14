"use client";

import { motion } from "framer-motion";

const STEPS = [
  {
    icon: "🏷️",
    title: "1. Conte sobre você",
    description:
      "Diga o nome do seu negócio e o jeito que você gosta de falar com seus clientes. Leva 1 minuto.",
  },
  {
    icon: "📸",
    title: "2. Mande suas fotos",
    description:
      "Tire foto dos seus produtos com o celular e arraste para a tela. Pode ser bolo, corte de cabelo, roupa, fruta — qualquer coisa.",
  },
  {
    icon: "✨",
    title: "3. Receba os posts prontos",
    description:
      "Em segundos você recebe a legenda, o título e as hashtags. É só copiar e colar no Instagram.",
  },
];

const cardVariants = {
  hidden: { opacity: 0, y: 50 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { type: "spring", stiffness: 80, damping: 16, delay: i * 0.15 },
  }),
};

export function HowItWorks() {
  return (
    <section id="como-funciona" className="section-pad bg-surface-900 py-24 lg:py-32">
      <div className="mx-auto max-w-9xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ type: "spring", stiffness: 80 }}
          className="mx-auto max-w-3xl text-center"
        >
          <h2 className="font-display text-[clamp(2rem,5vw,4rem)] font-extrabold leading-tight text-white">
            Só 3 passos. <span className="text-gradient">Sem complicação.</span>
          </h2>
          <p className="mt-5 text-[clamp(1.1rem,2vw,1.5rem)] text-white/55">
            Se você sabe tirar foto no celular, você sabe usar o AIPost.
          </p>
        </motion.div>

        <div className="mt-16 grid gap-7 md:grid-cols-3 lg:gap-10">
          {STEPS.map((step, i) => (
            <motion.div
              key={step.title}
              custom={i}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-60px" }}
              variants={cardVariants}
              whileHover={{ scale: 1.03, y: -6 }}
              className="glass flex flex-col items-center gap-5 rounded-3xl p-9 text-center transition-shadow hover:glow-purple-sm lg:p-12"
            >
              <div className="grid h-24 w-24 place-items-center rounded-3xl bg-gradient-to-br from-brand-600/30 to-brand-900/30 text-6xl lg:h-28 lg:w-28 lg:text-7xl">
                {step.icon}
              </div>
              <h3 className="font-display text-2xl font-bold text-white lg:text-3xl">
                {step.title}
              </h3>
              <p className="text-lg leading-relaxed text-white/60 lg:text-xl">
                {step.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
