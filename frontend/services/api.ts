import { API_URL, type FormatMap, type OutputFormat } from "@/lib/config";

export type ConversionResult = {
  blob: Blob;
  url: string;
  filename: string;
  format: OutputFormat;
  warnings: string[];
  markdown?: string;
};
export type ServerConfig = {
  max_file_size_mb: number;
  timeout_seconds: number;
  max_pdf_pages: number;
};

export async function getCapabilities(
  signal: AbortSignal,
): Promise<{ formats: FormatMap; config: ServerConfig }> {
  const [formatsResponse, configResponse] = await Promise.all([
    fetch(`${API_URL}/api/formats`, { signal, cache: "no-store" }),
    fetch(`${API_URL}/api/config`, { signal, cache: "no-store" }),
  ]);
  if (!formatsResponse.ok || !configResponse.ok)
    throw new Error(
      "O serviço de conversão está indisponível. Tente conectar novamente.",
    );
  return {
    formats: await formatsResponse.json(),
    config: await configResponse.json(),
  };
}

export function convertFile(
  file: File,
  output: OutputFormat,
  timeoutSeconds: number,
  onUpload: (percent: number) => void,
  onProcessing: () => void,
  onDownload: () => void,
) {
  const xhr = new XMLHttpRequest();
  const promise = new Promise<ConversionResult>((resolve, reject) => {
    xhr.open("POST", `${API_URL}/api/convert`);
    xhr.responseType = "blob";
    xhr.timeout = (timeoutSeconds + 60) * 1000;
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable)
        onUpload(Math.round((event.loaded / event.total) * 100));
    };
    xhr.upload.onload = () => onProcessing();
    xhr.onprogress = () => {
      if (xhr.status >= 200 && xhr.status < 300) onDownload();
    };
    xhr.onerror = () =>
      reject(
        new Error(
          "Não foi possível conectar ao conversor. Verifique sua conexão e tente novamente.",
        ),
      );
    xhr.ontimeout = () =>
      reject(
        new Error("O tempo de espera foi excedido. Tente um documento menor."),
      );
    xhr.onabort = () =>
      reject(new DOMException("Conversão cancelada.", "AbortError"));
    xhr.onload = async () => {
      try {
        const blob = xhr.response as Blob;
        if (xhr.status < 200 || xhr.status >= 300) {
          let detail = "Não foi possível concluir a conversão.";
          try {
            const body = JSON.parse(await blob.text());
            if (typeof body.detail === "string") detail = body.detail;
          } catch {
            /* retain safe message */
          }
          throw new Error(detail);
        }
        const disposition = xhr.getResponseHeader("Content-Disposition") || "";
        const encoded = disposition.match(/filename\*=utf-8''([^;]+)/i)?.[1];
        const plain = disposition.match(/filename="([^"]+)"/i)?.[1];
        const filename = encoded
          ? decodeURIComponent(encoded)
          : plain || file.name.replace(/\.[^.]+$/, "") + "." + output;
        let warnings: string[] = [];
        try {
          warnings = JSON.parse(
            decodeURIComponent(
              xhr.getResponseHeader("X-Conversion-Warnings") || "%5B%5D",
            ),
          );
        } catch {
          /* optional metadata */
        }
        const markdown =
          output === "md" && blob.size <= 5 * 1024 * 1024
            ? await blob.text()
            : undefined;
        resolve({
          blob,
          filename,
          format: output,
          warnings,
          markdown,
          url: URL.createObjectURL(blob),
        });
      } catch (error) {
        reject(error);
      }
    };
    const body = new FormData();
    body.append("file", file);
    body.append("output_format", output);
    xhr.send(body);
  });
  return { promise, abort: () => xhr.abort() };
}
