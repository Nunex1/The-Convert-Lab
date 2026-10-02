"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { type FormatMap, type OutputFormat } from "@/lib/config";
import {
  convertFile,
  getCapabilities,
  type ConversionResult,
  type ServerConfig,
} from "@/services/api";

export type Phase =
  | "idle"
  | "selected"
  | "uploading"
  | "processing"
  | "receiving"
  | "success"
  | "error";
export function useConverter() {
  const [formats, setFormats] = useState<FormatMap>({});
  const [config, setConfig] = useState<ServerConfig>({
    max_file_size_mb: 25,
    max_pdf_pages: 150,
    timeout_seconds: 120,
  });
  const [connection, setConnection] = useState<
    "loading" | "online" | "offline"
  >("loading");
  const [retry, setRetry] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [output, setOutput] = useState<OutputFormat | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [upload, setUpload] = useState(0);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ConversionResult | null>(null);
  const resultRef = useRef<ConversionResult | null>(null);
  const job = useRef<{ abort: () => void } | null>(null);
  const busyRef = useRef(false);
  const revision = useRef(0);
  const busy = ["uploading", "processing", "receiving"].includes(phase);
  const input = file?.name.split(".").pop()?.toLowerCase() || "";

  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    let current = true;
    setConnection("loading");
    getCapabilities(controller.signal)
      .then((data) => {
        if (current) {
          setFormats(data.formats);
          setConfig(data.config);
          setConnection("online");
        }
      })
      .catch(() => {
        if (current) setConnection("offline");
      })
      .finally(() => clearTimeout(timeout));
    return () => {
      current = false;
      clearTimeout(timeout);
      controller.abort();
    };
  }, [retry]);

  useEffect(
    () => () => {
      revision.current += 1;
      job.current?.abort();
      if (resultRef.current) URL.revokeObjectURL(resultRef.current.url);
    },
    [],
  );

  const clearResult = useCallback(() => {
    if (resultRef.current) URL.revokeObjectURL(resultRef.current.url);
    resultRef.current = null;
    setResult(null);
  }, []);

  function reset() {
    revision.current += 1;
    job.current?.abort();
    job.current = null;
    busyRef.current = false;
    clearResult();
    setFile(null);
    setOutput(null);
    setError("");
    setUpload(0);
    setPhase("idle");
  }

  function selectFile(candidate: File) {
    if (busyRef.current || connection !== "online") return;
    clearResult();
    setError("");
    setUpload(0);
    const extension = candidate.name.split(".").pop()?.toLowerCase() || "";
    if (
      !formats[extension] ||
      candidate.size > config.max_file_size_mb * 1024 * 1024 ||
      candidate.size === 0
    ) {
      setFile(null);
      setOutput(null);
      setPhase("error");
      setError(
        !formats[extension]
          ? "Este formato ainda não é suportado. Use PDF, DOCX, MHT ou MHTML."
          : candidate.size === 0
            ? "O arquivo está vazio. Selecione outro documento."
            : `O arquivo excede o limite de ${config.max_file_size_mb} MB.`,
      );
      return;
    }
    setFile(candidate);
    setOutput(formats[extension].length === 1 ? formats[extension][0] : null);
    setPhase("selected");
  }

  function selectOutput(value: OutputFormat) {
    if (busyRef.current || !formats[input]?.includes(value)) return;
    clearResult();
    setOutput(value);
    setError("");
    setPhase("selected");
  }

  async function convert() {
    if (!file || !output || busyRef.current) return;
    busyRef.current = true;
    const current = ++revision.current;
    clearResult();
    setError("");
    setUpload(0);
    setPhase("uploading");
    const request = convertFile(
      file,
      output,
      config.timeout_seconds,
      setUpload,
      () => setPhase("processing"),
      () => setPhase("receiving"),
    );
    job.current = request;
    try {
      const next = await request.promise;
      if (current !== revision.current) {
        URL.revokeObjectURL(next.url);
        return;
      }
      resultRef.current = next;
      setResult(next);
      setPhase("success");
    } catch (failure) {
      if (current !== revision.current) return;
      setError(
        failure instanceof Error
          ? failure.message
          : "Não foi possível concluir a conversão.",
      );
      setPhase("error");
    } finally {
      if (current === revision.current) {
        busyRef.current = false;
        job.current = null;
      }
    }
  }

  return {
    file,
    input,
    output,
    phase,
    upload,
    error,
    result,
    formats,
    config,
    connection,
    busy,
    selectFile,
    selectOutput,
    convert,
    reset,
    reconnect: () => setRetry((value) => value + 1),
  };
}
export type ConverterState = ReturnType<typeof useConverter>;
