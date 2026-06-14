export function SkeletonCard() {
  return (
    <div className="glass space-y-5 rounded-3xl p-7">
      {/* Título */}
      <div className="skeleton h-6 w-3/5 rounded-full" />

      {/* Linhas de legenda */}
      <div className="space-y-3">
        <div className="skeleton h-4 w-full rounded-full" />
        <div className="skeleton h-4 w-5/6 rounded-full" />
        <div className="skeleton h-4 w-2/3 rounded-full" />
      </div>

      {/* Dica */}
      <div className="skeleton h-16 w-full rounded-2xl" />

      {/* Hashtags */}
      <div className="flex flex-wrap gap-2">
        {[70, 90, 80].map((w) => (
          <div
            key={w}
            className="skeleton h-7 rounded-full"
            style={{ width: `${w}px` }}
          />
        ))}
      </div>

      {/* Botão */}
      <div className="skeleton h-12 w-full rounded-2xl" />
    </div>
  );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3 3xl:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
