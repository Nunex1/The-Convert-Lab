import { ArrowRight } from "lucide-react";

export function ConversionFlow({
  input,
  output,
}: {
  input: string;
  output: string | null;
}) {
  return (
    <div className="conversion-flow">
      <span>FLUXO</span>
      <div>
        <b>{input ? input.toUpperCase() : "ENTRADA"}</b>
        <ArrowRight size={16} />
        <b className={output ? "chosen" : ""}>
          {output?.toUpperCase() || "SAÍDA"}
        </b>
      </div>
      <span
        className={`flow-dot ${output ? "ready" : ""}`}
        aria-label={output ? "Formato escolhido" : "Aguardando seleção"}
      />
    </div>
  );
}
