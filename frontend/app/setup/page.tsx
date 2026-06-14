"use client";

import axios from "axios";
import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/ui/Navbar";
import { UploadZone } from "@/components/dashboard/UploadZone";
import { setupMarca } from "@/lib/api";
import { useToast } from "@/lib/toast-context";

const DEMO_CLIENT_ID = "00000000-0000-0000-0000-000000000001";

export default function SetupPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [step, setStep] = useState<1 | 2>(1);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    nomeMarca: "",
    tomVoz: "",
    nicho: "",
    descricao: "",
  });

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleBrandSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.nomeMarca || !form.tomVoz || !form.nicho) {
      toast("Preencha os campos marcados com * antes de continuar.", "error");
      return;
    }
    setSaving(true);
    try {
      await setupMarca({
        clienteId: DEMO_CLIENT_ID,
        nomeMarca: form.nomeMarca,
        tomVoz: form.tomVoz,
        nicho: form.nicho,
        descricao: form.descricao,
      });
      toast("Tudo certo! Agora mande suas fotos.", "success");
      setStep(2);
    } catch (error: unknown) {
      const detail = axios.isAxiosError(error)
        ? ((error.response?.data as { detail?: string } | undefined)?.detail ??
          error.message)
        : error instanceof Error
          ? error.message
          : "Erro desconhecido";
      toast(`Erro ao salvar: ${detail}`, "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Navbar />

      <main className="relative min-h-screen bg-surface-900 py-12 lg:py-16">
        <div
          className="pointer-events-none fixed inset-0"
          style={{
            background:
              "radial-gradient(ellipse 60% 40% at 30% 15%, rgba(124,58,237,0.1) 0%, transparent 70%)",
          }}
        />

        <div className="section-pad relative mx-auto max-w-3xl">
          {/* Barra de progresso grande e clara */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-10 text-center"
          >
            <div className="mx-auto mb-6 flex max-w-md items-center gap-3">
              {[
                { n: 1, label: "Seu negócio" },
                { n: 2, label: "Suas fotos" },
              ].map((s, idx) => (
                <div key={s.n} className="flex flex-1 items-center gap-3">
                  <div className="flex flex-1 flex-col items-center gap-2">
                    <div
                      className={[
                        "grid h-12 w-12 place-items-center rounded-full text-xl font-bold transition-colors",
                        s.n <= step
                          ? "bg-brand-600 text-white"
                          : "bg-white/10 text-white/40",
                      ].join(" ")}
                    >
                      {s.n < step ? "✓" : s.n}
                    </div>
                    <span
                      className={[
                        "text-sm font-medium",
                        s.n <= step ? "text-white" : "text-white/40",
                      ].join(" ")}
                    >
                      {s.label}
                    </span>
                  </div>
                  {idx === 0 && (
                    <div
                      className={[
                        "h-1 flex-1 rounded-full transition-colors",
                        step > 1 ? "bg-brand-500" : "bg-white/10",
                      ].join(" ")}
                    />
                  )}
                </div>
              ))}
            </div>

            <h1 className="font-display text-[clamp(1.8rem,4.5vw,3rem)] font-extrabold leading-tight text-white">
              {step === 1 ? "Conte sobre o seu negócio" : "Agora, suas fotos"}
            </h1>
            <p className="mt-3 text-[clamp(1rem,2vw,1.35rem)] text-white/55">
              {step === 1
                ? "Não precisa caprichar — escreva do seu jeito mesmo."
                : "Tire foto dos seus produtos e arraste para a área abaixo."}
            </p>
          </motion.div>

          {/* Passo 1 */}
          {step === 1 && (
            <motion.form
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              onSubmit={handleBrandSubmit}
              className="glass-strong space-y-7 rounded-3xl p-7 lg:p-10"
            >
              <Field
                label="Qual o nome do seu negócio?"
                required
                name="nomeMarca"
                placeholder="Ex: Bolos da Vovó"
                example="Pode ser o nome da sua loja, marca ou o seu próprio nome."
                value={form.nomeMarca}
                onChange={handleChange}
              />
              <Field
                label="Como você gosta de falar com seus clientes?"
                required
                name="tomVoz"
                placeholder="Ex: De um jeito caseiro, carinhoso e animado"
                example="Sério e profissional? Brincalhão e jovem? Escreva como você fala."
                value={form.tomVoz}
                onChange={handleChange}
              />
              <Field
                label="O que você vende?"
                required
                name="nicho"
                placeholder="Ex: Bolos e doces caseiros"
                example="Tipo: cortes de cabelo, roupas, frutas, comida, unhas..."
                value={form.nicho}
                onChange={handleChange}
              />

              <div className="space-y-2">
                <label
                  htmlFor="descricao"
                  className="block text-lg font-semibold text-white"
                >
                  Quer contar mais alguma coisa?{" "}
                  <span className="text-base font-normal text-white/40">
                    (opcional)
                  </span>
                </label>
                <textarea
                  id="descricao"
                  name="descricao"
                  placeholder="Ex: Faço bolos de vários sabores, tudo feito à mão com muito amor."
                  value={form.descricao}
                  onChange={handleChange}
                  rows={3}
                  className="w-full resize-none rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-white placeholder-white/30 transition focus:border-brand-500 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={saving}
                className="glow-purple-sm flex w-full items-center justify-center gap-2 rounded-2xl bg-brand-600 py-5 text-xl font-bold text-white transition-all hover:scale-[1.01] hover:bg-brand-500 disabled:scale-100 disabled:opacity-60"
              >
                {saving ? "Salvando…" : "Continuar →"}
              </button>
            </motion.form>
          )}

          {/* Passo 2 */}
          {step === 2 && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div className="glass-strong rounded-3xl p-7 lg:p-10">
                <UploadZone clienteId={DEMO_CLIENT_ID} />
              </div>

              <button
                onClick={() => router.push("/dashboard")}
                className="glow-purple-sm mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-brand-600 py-5 text-xl font-bold text-white transition-all hover:scale-[1.01] hover:bg-brand-500"
              >
                Já mandei minhas fotos, criar posts! →
              </button>
              <button
                onClick={() => setStep(1)}
                className="mt-3 w-full py-3 text-lg font-medium text-white/50 transition-colors hover:text-white"
              >
                ← Voltar
              </button>
            </motion.div>
          )}
        </div>
      </main>
    </>
  );
}

function Field({
  label,
  name,
  placeholder,
  example,
  value,
  onChange,
  required,
}: {
  label: string;
  name: string;
  placeholder: string;
  example?: string;
  value: string;
  onChange: React.ChangeEventHandler<HTMLInputElement>;
  required?: boolean;
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={name} className="block text-lg font-semibold text-white">
        {label} {required && <span className="text-brand-400">*</span>}
      </label>
      {example && <p className="text-base text-white/45">{example}</p>}
      <input
        id={name}
        type="text"
        name={name}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className="w-full rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-white placeholder-white/30 transition focus:border-brand-500 focus:outline-none"
      />
    </div>
  );
}
