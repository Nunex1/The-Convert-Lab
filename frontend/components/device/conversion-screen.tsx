import {
  ArrowRight,
  Check,
  FileText,
  TriangleAlert,
  ScanLine,
} from "lucide-react";
import type { ConverterState } from "@/hooks/use-converter";
import { fileSize } from "@/lib/config";
import { ConversionProgress } from "./conversion-progress";

export function ConversionScreen({ state }: { state: ConverterState }) {
  const { phase, file, input, output, result, error, busy } = state;
  const title =
    phase === "error"
      ? "Conversão interrompida"
      : phase === "success"
        ? "Conversão concluída"
        : busy
          ? "Transformando seu arquivo"
          : file
            ? "Tudo pronto para começar"
            : "Pronto para converter";
  return (
    <div className={`conversion-screen screen-${phase}`}>
      <div className="screen-topline">
        <span>
          <i /> MONITOR DE CONVERSÃO
        </span>
        <span>01 / STATUS</span>
      </div>
      <div className="screen-main">
        <div
          className={`file-orbit ${busy ? "is-busy" : ""}`}
          aria-hidden="true"
        >
          <span className="orbit-corner tl" />
          <span className="orbit-corner tr" />
          <span className="orbit-corner bl" />
          <span className="orbit-corner br" />
          <div className="document-glyph">
            {phase === "success" ? (
              <Check size={45} strokeWidth={1.3} />
            ) : phase === "error" ? (
              <TriangleAlert size={42} strokeWidth={1.3} />
            ) : busy ? (
              <ScanLine size={44} strokeWidth={1.2} />
            ) : (
              <FileText size={44} strokeWidth={1.2} />
            )}
          </div>
          <span className="glyph-caption">
            {phase === "success"
              ? result?.format.toUpperCase()
              : file
                ? input.toUpperCase()
                : "FILE / IN"}
          </span>
        </div>
        <div className="screen-message" aria-live="polite" aria-atomic="true">
          <h2>{title}</h2>
          <p>
            {phase === "error"
              ? error
              : phase === "success"
                ? "Um novo formato. Todas as possibilidades."
                : busy
                  ? "Pode deixar com a gente."
                  : file
                    ? "Escolha o formato de saída e inicie a conversão."
                    : "Seu próximo formato começa aqui."}
          </p>
        </div>
        {file ? (
          <div className="file-telemetry">
            <span
              className="telemetry-name"
              title={result?.filename || file.name}
            >
              {result?.filename || file.name}
            </span>
            <span className="telemetry-meta">
              {input.toUpperCase()} <ArrowRight size={12} />{" "}
              {output?.toUpperCase() || "…"} <i />{" "}
              {fileSize(result?.blob.size || file.size)}
            </span>
          </div>
        ) : (
          <div className="idle-formats">
            <span>PDF</span>
            <span>DOCX</span>
            <span>MHT</span>
            <span>MHTML</span>
          </div>
        )}
      </div>
      <ConversionProgress phase={phase} upload={state.upload} />
    </div>
  );
}
