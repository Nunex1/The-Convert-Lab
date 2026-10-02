"use client";
import { useState } from "react";
import { Download, Eye, Copy, Check, RotateCcw } from "lucide-react";
import dynamic from "next/dynamic";
import type { ConversionResult } from "@/services/api";
const MarkdownPreview = dynamic(() => import("@/components/markdown-preview"), {
  ssr: false,
});

export function DownloadResult({
  result,
  reset,
}: {
  result: ConversionResult;
  reset: () => void;
}) {
  const [preview, setPreview] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");
  async function copy() {
    try {
      await navigator.clipboard.writeText(result.markdown || "");
      setCopied(true);
      setCopyError("");
    } catch {
      setCopyError(
        "Não foi possível copiar. Abra a visualização e copie o código.",
      );
    }
  }
  return (
    <div className="download-result">
      <a
        className="primary-button download-button"
        href={result.url}
        download={result.filename}
      >
        <Download size={18} /> Baixar {result.format.toUpperCase()}
        <span>↗</span>
      </a>
      {result.markdown !== undefined && (
        <div className="markdown-actions">
          <button onClick={() => setPreview(true)}>
            <Eye size={14} /> Visualizar
          </button>
          <button onClick={copy}>
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? "Copiado" : "Copiar Markdown"}
          </button>
        </div>
      )}
      {result.format === "md" && result.markdown === undefined && (
        <p className="inline-notice">
          Prévia limitada a 5 MB. Baixe para visualizar o documento completo.
        </p>
      )}
      {copyError && (
        <p role="status" className="inline-notice">
          {copyError}
        </p>
      )}
      <button className="reset-button" onClick={reset}>
        <RotateCcw size={13} /> Converter outro arquivo
      </button>
      {preview && (
        <MarkdownPreview
          text={result.markdown || ""}
          name={result.filename}
          onClose={() => setPreview(false)}
        />
      )}
    </div>
  );
}
