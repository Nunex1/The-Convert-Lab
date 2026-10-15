import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { CsvOptions } from "@/components/device/csv-options";
import { OutputFormatSelector } from "@/components/device/output-format-selector";
import { ConversionProgress } from "@/components/device/conversion-progress";
import { DEFAULT_CSV_OPTIONS, convertFile } from "@/services/api";

describe("Exportação de planilhas", () => {
  it("mostra somente saídas anunciadas para XLSX", () => {
    render(<OutputFormatSelector formats={["csv"]} selected="csv" disabled={false} hasFile onSelect={vi.fn()} />);
    expect(screen.getByRole("button", { name: /CSV/ })).toBeEnabled();
    expect(screen.queryByRole("button", { name: /binário/ })).toBeNull();
  });
  it("informa perdas e permite escolher aba, BOM, delimitador e proteção", () => {
    const change = vi.fn();
    render(<CsvOptions value={DEFAULT_CSV_OPTIONS} onChange={change} disabled={false} />);
    expect(screen.getByText(/as demais não serão incluídas/)).toBeVisible();
    fireEvent.change(screen.getByLabelText(/Nome exato/), { target: { value: "Dados" } });
    expect(change).toHaveBeenLastCalledWith({ ...DEFAULT_CSV_OPTIONS, sheet: "Dados" });
    fireEvent.change(screen.getByLabelText("Separador"), { target: { value: "," } });
    expect(change).toHaveBeenLastCalledWith({ ...DEFAULT_CSV_OPTIONS, delimiter: "," });
    fireEvent.click(screen.getByLabelText("BOM para Excel"));
    expect(change).toHaveBeenLastCalledWith({ ...DEFAULT_CSV_OPTIONS, bom: true });
    fireEvent.click(screen.getByLabelText(/Proteger textos/));
    expect(change).toHaveBeenLastCalledWith({ ...DEFAULT_CSV_OPTIONS, protect_formulas: false });
  });
  it("bloqueia alterações durante a conversão", () => {
    render(<CsvOptions value={DEFAULT_CSV_OPTIONS} onChange={vi.fn()} disabled />);
    expect(screen.getByLabelText("Separador")).toBeDisabled();
    expect(screen.getByLabelText(/Nome exato/)).toBeDisabled();
  });
  it.each(["processing", "receiving"] as const)("não inventa percentual em %s", phase => {
    render(<ConversionProgress phase={phase} upload={100} />);
    expect(screen.getByRole("progressbar")).not.toHaveAttribute("aria-valuenow");
    expect(screen.queryByText("100%")).toBeNull();
  });
  it("envia as opções no mesmo upload e preserva cancelamento", () => {
    const send = vi.fn(), abort = vi.fn();
    vi.stubGlobal("XMLHttpRequest", class {
      upload = {}; open = vi.fn(); send = send; abort = abort;
    });
    try {
      const request = convertFile(new File(["xlsx"], "dados.xlsx"), "csv", 120, vi.fn(), vi.fn(), vi.fn(), { ...DEFAULT_CSV_OPTIONS, sheet: "Dados" });
      expect(send).toHaveBeenCalledTimes(1);
      expect(JSON.parse(send.mock.calls[0][0].get("csv_options"))).toEqual({ ...DEFAULT_CSV_OPTIONS, sheet: "Dados" });
      request.abort();
      expect(abort).toHaveBeenCalledTimes(1);
    } finally { vi.unstubAllGlobals(); }
  });
});
