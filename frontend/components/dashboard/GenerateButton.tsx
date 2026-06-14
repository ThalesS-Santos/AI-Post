"use client";

import { motion, AnimatePresence } from "framer-motion";

interface GenerateButtonProps {
  onClick: () => void;
  loading: boolean;
  disabled?: boolean;
}

export function GenerateButton({ onClick, loading, disabled }: GenerateButtonProps) {
  const inactive = loading || disabled;

  return (
    <motion.button
      onClick={onClick}
      disabled={inactive}
      whileHover={!inactive ? { scale: 1.03 } : undefined}
      whileTap={!inactive ? { scale: 0.97 } : undefined}
      transition={{ type: "spring", stiffness: 400, damping: 20 }}
      className={[
        "flex items-center justify-center gap-3 rounded-2xl px-10 py-5 text-xl font-bold text-white transition-colors lg:text-2xl",
        inactive
          ? "cursor-not-allowed bg-brand-700/50 opacity-70"
          : "glow-purple-sm bg-brand-600 hover:bg-brand-500",
      ].join(" ")}
    >
      <AnimatePresence mode="wait">
        {loading ? (
          <motion.span
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-3"
          >
            <svg
              className="h-6 w-6 animate-spin text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Criando…
          </motion.span>
        ) : (
          <motion.span
            key="idle"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2 whitespace-nowrap"
          >
            ✨ Criar meus posts
          </motion.span>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
