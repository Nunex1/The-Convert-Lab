import type { Phase } from "@/hooks/use-converter";

export function StatusIndicators({ phase }: { phase: Phase }) {
  const current =
    phase === "uploading"
      ? 0
      : phase === "processing"
        ? 1
        : phase === "receiving" || phase === "success"
          ? 2
          : -1;
  return (
    <div className="status-indicators" aria-label="Etapas da conversão">
      {["Envio", "Conversão", "Arquivo"].map((name, index) => (
        <span
          key={name}
          className={
            index === current
              ? `indicator active ${phase === "success" ? "done" : ""}`
              : index < current
                ? "indicator complete"
                : "indicator"
          }
        >
          <i aria-hidden="true" />
          {name}
        </span>
      ))}
    </div>
  );
}
