import Link from "next/link";
import { Navbar } from "@/components/ui/Navbar";
import { HeroSection } from "@/components/welcome/HeroSection";
import { HowItWorks } from "@/components/welcome/HowItWorks";
import { ForWho } from "@/components/welcome/ForWho";

export default function WelcomePage() {
  return (
    <>
      <Navbar cta={{ label: "Entrar", href: "/login" }} />

      <main>
        <HeroSection />
        <HowItWorks />
        <ForWho />

        {/* CTA final */}
        <section className="section-pad relative overflow-hidden bg-surface-900 py-28 text-center lg:py-36">
          <div
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(ellipse 70% 60% at 50% 50%, rgba(124,58,237,0.18) 0%, transparent 70%)",
            }}
          />
          <div className="relative mx-auto max-w-4xl">
            <h2 className="font-display text-[clamp(2.2rem,6vw,5rem)] font-extrabold leading-tight text-white">
              Bora começar?
            </h2>
            <p className="mx-auto mt-6 max-w-2xl text-[clamp(1.1rem,2.2vw,1.6rem)] text-white/60">
              Configure seu negócio em 2 minutos e crie sua primeira leva de
              posts agora mesmo. É de graça.
            </p>
            <Link
              href="/login"
              className="glow-purple mt-12 inline-flex items-center justify-center gap-3 rounded-2xl bg-brand-600 px-12 py-6 text-2xl font-bold text-white transition-all hover:scale-[1.03] hover:bg-brand-500"
            >
              Criar meus posts grátis →
            </Link>
          </div>
        </section>

        {/* Rodapé */}
        <footer className="section-pad border-t border-white/10 bg-surface-800 py-10">
          <div className="mx-auto flex max-w-9xl flex-col items-center justify-between gap-4 text-center md:flex-row md:text-left">
            <p className="font-display text-2xl font-extrabold text-white">
              AI<span className="text-brand-400">Post</span>
            </p>
            <p className="text-base text-white/40">
              © 2026 AIPost · Conteúdo para o seu negócio
            </p>
          </div>
        </footer>
      </main>
    </>
  );
}
