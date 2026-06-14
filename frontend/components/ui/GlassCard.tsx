"use client";

import { motion, HTMLMotionProps } from "framer-motion";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  glowOnHover?: boolean;
}

export function GlassCard({
  children,
  className,
  glowOnHover = false,
  ...props
}: GlassCardProps) {
  return (
    <motion.div
      whileHover={
        glowOnHover
          ? { scale: 1.03, y: -4 }
          : undefined
      }
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className={twMerge(
        clsx(
          "glass rounded-2xl p-6 transition-shadow duration-300",
          glowOnHover && "hover:glow-purple-sm cursor-pointer"
        ),
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}
