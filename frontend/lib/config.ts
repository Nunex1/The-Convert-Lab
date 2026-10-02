export const BRAND = "ConvertLab";
export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");
export type OutputFormat = "md" | "docx" | "xlsx" | "pptx";
export type FormatMap = Record<string, OutputFormat[]>;
export const FORMAT_NAMES: Record<OutputFormat, string> = {
  md: "Markdown",
  docx: "Word",
  xlsx: "Excel",
  pptx: "PowerPoint",
};
export const FORMAT_DETAILS: Record<OutputFormat, string> = {
  md: "Texto estruturado",
  docx: "Documento editável",
  xlsx: "Dados e tabelas",
  pptx: "Apresentação",
};
export const ACCEPTED = ".pdf,.docx,.mht,.mhtml";
export function fileSize(bytes: number) {
  return bytes >= 1024 * 1024
    ? `${(bytes / 1024 / 1024).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} MB`
    : `${Math.max(1, bytes / 1024).toLocaleString("pt-BR", { maximumFractionDigits: 0 })} KB`;
}
