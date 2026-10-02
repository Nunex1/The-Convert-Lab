import { ArrowRight, LoaderCircle, Radio, RotateCw, Info } from "lucide-react";
import type { ConverterState } from "@/hooks/use-converter";
import { FileSelector } from "./file-selector";
import { OutputFormatSelector } from "./output-format-selector";
import { ConversionFlow } from "./conversion-flow";
import { DownloadResult } from "./download-result";
import { PrivacyStatus } from "./privacy-status";

export function DeviceRightPanel({ state }: { state: ConverterState }) {
  return (
    <section
      className="device-panel right-panel"
      aria-label="Controles do conversor"
    >
      <div className="right-hardware-header">
        <h2>CONVERSOR</h2>
        <span>
          <Radio size={13} />{" "}
          {state.connection === "online"
            ? "ONLINE"
            : state.connection === "loading"
              ? "CONECTANDO"
              : "OFFLINE"}
        </span>
      </div>
      <div className="control-screen">
        {state.connection === "offline" && (
          <div className="connection-error" role="alert">
            <p>Serviço de conversão indisponível.</p>
            <button onClick={state.reconnect}>
              <RotateCw size={13} /> Reconectar
            </button>
          </div>
        )}
        <FileSelector
          file={state.file}
          disabled={state.busy || state.connection !== "online"}
          maxSize={state.config.max_file_size_mb}
          onSelect={state.selectFile}
          onRemove={state.reset}
        />
        <OutputFormatSelector
          formats={state.formats[state.input] || []}
          selected={state.output}
          disabled={state.busy}
          hasFile={!!state.file}
          onSelect={state.selectOutput}
        />
        <ConversionFlow input={state.input} output={state.output} />
        {state.result ? (
          <DownloadResult result={state.result} reset={state.reset} />
        ) : (
          <>
            <button
              className="primary-button"
              disabled={
                !state.file ||
                !state.output ||
                state.busy ||
                state.connection !== "online"
              }
              onClick={state.convert}
            >
              {state.busy ? (
                <>
                  <LoaderCircle className="spin" size={17} /> Convertendo
                  arquivo
                </>
              ) : (
                <>
                  Converter arquivo <ArrowRight size={18} />
                </>
              )}
            </button>
            <p className="action-caption">
              {state.busy
                ? "Mantenha esta página aberta até concluir."
                : !state.file
                  ? "Selecione um arquivo para começar"
                  : !state.output
                    ? "Escolha um formato de saída"
                    : "Seu arquivo está pronto para ser convertido"}
            </p>
          </>
        )}
        {state.result?.warnings.map((message, index) => (
          <p className="result-warning" key={index}>
            <Info size={14} />
            <span>{message}</span>
          </p>
        ))}
        <PrivacyStatus />
      </div>
    </section>
  );
}
