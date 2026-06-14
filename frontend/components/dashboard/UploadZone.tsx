"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { uploadProduto } from "@/lib/api";
import { useToast } from "@/lib/toast-context";

interface UploadZoneProps {
  clienteId: string;
  onUploaded?: (url: string) => void;
}

export function UploadZone({ clienteId, onUploaded }: UploadZoneProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [textoBase, setTextoBase] = useState("");
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const { toast } = useToast();

  const onDrop = useCallback((accepted: File[]) => {
    const file = accepted[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setPendingFile(file);
    setProgress(0);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [".jpg", ".jpeg", ".png", ".webp"] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  async function handleUpload() {
    if (!pendingFile || !textoBase.trim()) {
      toast("Escreva o que é a foto antes de enviar.", "error");
      return;
    }
    setUploading(true);
    try {
      const { url } = await uploadProduto(
        clienteId,
        pendingFile,
        textoBase,
        (pct) => setProgress(pct)
      );
      toast("Foto adicionada! Pode mandar outra ou seguir em frente.", "success");
      onUploaded?.(url);
      setPreview(null);
      setPendingFile(null);
      setTextoBase("");
      setProgress(0);
    } catch {
      toast("Não consegui enviar a foto. Tente de novo.", "error");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Área de arrastar */}
      <div
        {...getRootProps()}
        className={[
          "relative cursor-pointer rounded-3xl border-4 border-dashed p-10 text-center transition-all duration-200 lg:p-14",
          isDragActive
            ? "scale-[1.01] border-brand-500 bg-brand-900/25"
            : "border-white/20 hover:border-brand-600/70 hover:bg-white/[0.03]",
        ].join(" ")}
      >
        <input {...getInputProps()} />

        <AnimatePresence mode="wait">
          {preview ? (
            <motion.div
              key="preview"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-4"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={preview}
                alt="Sua foto"
                className="max-h-64 rounded-2xl object-contain shadow-xl"
              />
              <p className="text-lg text-white/55">
                Toque aqui para trocar a foto
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-4 py-4"
            >
              <span className="text-7xl lg:text-8xl">
                {isDragActive ? "📥" : "📷"}
              </span>
              <p className="text-2xl font-bold text-white">
                {isDragActive
                  ? "Pode soltar!"
                  : "Toque para escolher uma foto"}
              </p>
              <p className="text-lg text-white/45">
                ou arraste a imagem para cá
              </p>
              <p className="text-base text-white/30">
                Formatos: JPG, PNG · até 10MB
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* O que é a foto */}
      <div className="space-y-2">
        <label
          htmlFor="texto-produto"
          className="block text-lg font-semibold text-white"
        >
          O que é essa foto?
        </label>
        <input
          id="texto-produto"
          type="text"
          placeholder="Ex: Brigadeiro de morango com cobertura de chocolate"
          value={textoBase}
          onChange={(e) => setTextoBase(e.target.value)}
          className="w-full rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-lg text-white placeholder-white/30 transition focus:border-brand-500 focus:outline-none"
        />
      </div>

      {/* Barra de progresso */}
      {uploading && (
        <div className="h-3 w-full overflow-hidden rounded-full bg-white/10">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-brand-600 to-brand-400"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{ ease: "easeOut" }}
          />
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!pendingFile || uploading}
        className="flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-brand-600/60 bg-brand-900/20 py-4 text-lg font-bold text-white transition-colors hover:bg-brand-900/40 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {uploading ? `Enviando… ${progress}%` : "➕ Adicionar esta foto"}
      </button>
    </div>
  );
}
