import type { Phase } from "@/hooks/use-converter";

export function StatusLens({
  phase,
  online,
}: {
  phase: Phase;
  online: boolean;
}) {
  const status = !online
    ? "offline"
    : phase === "success"
      ? "success"
      : phase === "error"
        ? "error"
        : ["uploading", "processing", "receiving"].includes(phase)
          ? "busy"
          : "ready";
  const labels = {
    offline: "Serviço desconectado",
    success: "Conversão concluída",
    error: "Atenção: erro na conversão",
    busy: "Conversão em andamento",
    ready: "Sistema pronto",
  };
  return (
    <span
      className={`lens-ring lens-${status}`}
      role="img"
      aria-label={labels[status]}
      title={labels[status]}
    >
      <span className="lens" />
    </span>
  );
}
