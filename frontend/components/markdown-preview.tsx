"use client";
import { useEffect, useRef, useState } from "react";
import { X, Code2, Eye } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MarkdownPreview({
  text,
  name,
  onClose,
}: {
  text: string;
  name: string;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [tab, setTab] = useState<"preview" | "code">("preview");
  useEffect(() => {
    const element = dialog.current;
    element?.showModal();
    return () => element?.close();
  }, []);
  return (
    <dialog
      className="markdown-dialog"
      ref={dialog}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      aria-labelledby="preview-title"
    >
      <div className="preview-header">
        <div>
          <span className="eyebrow">RESULTADO / MARKDOWN</span>
          <h2 id="preview-title">{name}</h2>
        </div>
        <button
          autoFocus
          onClick={onClose}
          className="icon-button"
          aria-label="Fechar visualização"
        >
          <X size={22} />
        </button>
      </div>
      <div className="preview-tabs" aria-label="Modo de visualização">
        <button
          aria-pressed={tab === "preview"}
          onClick={() => setTab("preview")}
        >
          <Eye size={15} /> Visualização
        </button>
        <button aria-pressed={tab === "code"} onClick={() => setTab("code")}>
          <Code2 size={15} /> Código
        </button>
      </div>
      <div className="preview-body">
        {tab === "code" ? (
          <pre tabIndex={0}>{text}</pre>
        ) : (
          <article className="markdown-body">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              skipHtml
              components={{
                img: ({ alt }) => (
                  <span className="image-placeholder">
                    [Imagem incorporada: {alt || "sem descrição"}. Disponível no
                    arquivo baixado.]
                  </span>
                ),
                a: ({ children, href }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {text}
            </ReactMarkdown>
          </article>
        )}
      </div>
      <p className="preview-note">
        Imagens não são carregadas na prévia para proteger sua privacidade.
      </p>
    </dialog>
  );
}
