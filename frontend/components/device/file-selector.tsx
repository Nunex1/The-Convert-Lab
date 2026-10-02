"use client";
import { useRef, useState } from "react";
import { FileText, Upload, X } from "lucide-react";
import { ACCEPTED, fileSize } from "@/lib/config";

export function FileSelector({
  file,
  disabled,
  maxSize,
  onSelect,
  onRemove,
}: {
  file: File | null;
  disabled: boolean;
  maxSize: number;
  onSelect: (file: File) => void;
  onRemove: () => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [notice, setNotice] = useState("");
  function accept(files: FileList | null) {
    if (!files?.length || disabled) return;
    if (files.length > 1) {
      setNotice("Selecione um arquivo por vez.");
      return;
    }
    setNotice("");
    onSelect(files[0]);
    if (input.current) input.current.value = "";
  }
  return (
    <div className="file-selector">
      <div className="field-label">
        <span>
          01 <b>ARQUIVO DE ENTRADA</b>
        </span>
        <span>ATÉ {maxSize} MB</span>
      </div>
      <input
        ref={input}
        id="file-upload"
        type="file"
        accept={ACCEPTED}
        onChange={(event) => accept(event.target.files)}
        disabled={disabled}
        className="sr-only"
        tabIndex={-1}
        aria-label="Selecionar arquivo"
      />
      <div
        className={`drop-zone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""} ${disabled ? "disabled" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node))
            setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          accept(event.dataTransfer.files);
        }}
      >
        {file ? (
          <>
            <div className="selected-file-icon">
              <FileText size={22} />
            </div>
            <div className="selected-file-info">
              <strong title={file.name}>{file.name}</strong>
              <span>
                {file.name.split(".").pop()?.toUpperCase()} <i />{" "}
                {fileSize(file.size)}
              </span>
            </div>
            <button
              className="remove-file"
              disabled={disabled}
              onClick={onRemove}
              aria-label="Remover arquivo"
            >
              <X size={17} />
            </button>
          </>
        ) : (
          <button
            type="button"
            className="upload-target"
            disabled={disabled}
            onClick={() => input.current?.click()}
          >
            <span className="upload-icon">
              <Upload size={23} strokeWidth={1.5} />
            </span>
            <strong>
              {dragging ? "Solte o arquivo aqui" : "Arraste seu arquivo aqui"}
            </strong>
            <span>
              ou <u>selecione do computador</u>
            </span>
            <small>PDF, DOCX, MHT ou MHTML</small>
          </button>
        )}
      </div>
      {notice && (
        <p className="inline-notice" role="alert">
          {notice}
        </p>
      )}
    </div>
  );
}
