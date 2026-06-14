"use client";

import { motion } from "framer-motion";

const PEOPLE = [
  { icon: "💈", label: "Barbeiro" },
  { icon: "🥦", label: "Feirante" },
  { icon: "🧁", label: "Confeiteiro" },
  { icon: "👗", label: "Loja de roupa" },
  { icon: "💅", label: "Manicure" },
  { icon: "🍔", label: "Lanchonete" },
  { icon: "🌻", label: "Floricultura" },
  { icon: "🛠️", label: "Autônomo" },
];

export function ForWho() {
  return (
    <section className="section-pad bg-surface-800 py-24 lg:py-32">
      <div className="mx-auto max-w-9xl">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ type: "spring", stiffness: 80 }}
          className="mx-auto max-w-3xl text-center"
        >
          <h2 className="font-display text-[clamp(2rem,5vw,4rem)] font-extrabold leading-tight text-white">
            Feito para <span className="text-gradient">todo mundo</span>
          </h2>
          <p className="mt-5 text-[clamp(1.1rem,2vw,1.5rem)] text-white/55">
            Não importa o seu negócio nem a sua idade. Se você vende algo, a
            AIPost te ajuda a divulgar.
          </p>
        </motion.div>

        <div className="mt-16 grid grid-cols-2 gap-5 sm:grid-cols-4 lg:gap-7">
          {PEOPLE.map((p, i) => (
            <motion.div
              key={p.label}
              initial={{ opacity: 0, scale: 0.85 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06, type: "spring", stiffness: 120 }}
              className="glass flex flex-col items-center gap-4 rounded-3xl p-8 text-center lg:p-10"
            >
              <span className="text-6xl lg:text-7xl">{p.icon}</span>
              <span className="text-xl font-semibold text-white/85 lg:text-2xl">
                {p.label}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
