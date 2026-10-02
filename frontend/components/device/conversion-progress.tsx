import type { Phase } from "@/hooks/use-converter";

export function ConversionProgress({
  phase,
  upload,
}: {
  phase: Phase;
  upload: number;
}) {
  const complete = phase === "success";
  const uploading = phase === "uploading";
  const busy = phase === "processing" || phase === "receiving";
  const labels = {
    idle: "Aguardando arquivo",
    selected: "Arquivo pronto",
    uploading: "Enviando arquivo",
    processing: "Processando no servidor",
    receiving: "Recebendo resultado",
    success: "Arquivo pronto para baixar",
    error: "Processamento interrompido",
  };
  return (
    <div className={`conversion-progress ${complete ? "completed" : ""}`}>
      <div className="progress-heading">
        <span>{labels[phase]}</span>
        <strong>
          {complete
            ? "100%"
            : uploading
              ? `${upload}%`
              : busy
                ? "EM ANDAMENTO"
                : "—"}
        </strong>
      </div>
      <div
        className={`progress-track ${busy ? "indeterminate" : ""}`}
        role="progressbar"
        aria-label={uploading ? "Progresso do envio" : "Estado da conversão"}
        aria-valuenow={complete ? 100 : uploading ? upload : undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={labels[phase]}
      >
        <span
          style={{
            width: complete
              ? "100%"
              : uploading
                ? `${upload}%`
                : busy
                  ? "35%"
                  : "0%",
          }}
        />
      </div>
      <div className="progress-caption">
        {busy
          ? "O tempo depende do tamanho e da estrutura do arquivo."
          : uploading
            ? "Percentual real do envio do arquivo."
            : complete
              ? "Conversão finalizada e arquivo validado."
              : "Envie. Escolha. Converta."}
      </div>
    </div>
  );
}
