import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FileSelector } from "@/components/device/file-selector";
import { OutputFormatSelector } from "@/components/device/output-format-selector";
import { ConversionProgress } from "@/components/device/conversion-progress";
import { ConversionScreen } from "@/components/device/conversion-screen";
import type { ConverterState } from "@/hooks/use-converter";

describe("Upload acessível e drag and drop", () => {
  it("recebe um arquivo solto na área de upload", () => {
    const onSelect = vi.fn();
    render(
      <FileSelector
        file={null}
        disabled={false}
        maxSize={25}
        onSelect={onSelect}
        onRemove={vi.fn()}
      />,
    );
    const file = new File(["%PDF-1.7"], "documento.pdf", {
      type: "application/pdf",
    });
    fireEvent.drop(
      screen.getByRole("button", { name: /Arraste seu arquivo/ })
        .parentElement!,
      { dataTransfer: { files: [file] } },
    );
    expect(onSelect).toHaveBeenCalledWith(file);
  });
  it("explica a restrição de múltiplos arquivos", () => {
    const onSelect = vi.fn();
    render(
      <FileSelector
        file={null}
        disabled={false}
        maxSize={25}
        onSelect={onSelect}
        onRemove={vi.fn()}
      />,
    );
    fireEvent.drop(
      screen.getByRole("button", { name: /Arraste seu arquivo/ })
        .parentElement!,
      {
        dataTransfer: {
          files: [new File(["a"], "a.pdf"), new File(["b"], "b.pdf")],
        },
      },
    );
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Selecione um arquivo por vez.",
    );
  });
  it("impede substituição durante o processamento", () => {
    const onSelect = vi.fn();
    render(
      <FileSelector
        file={null}
        disabled
        maxSize={25}
        onSelect={onSelect}
        onRemove={vi.fn()}
      />,
    );
    fireEvent.drop(
      screen.getByRole("button", { name: /Arraste seu arquivo/ })
        .parentElement!,
      { dataTransfer: { files: [new File(["a"], "a.pdf")] } },
    );
    expect(onSelect).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: /Arraste seu arquivo/ }),
    ).toBeDisabled();
  });
  it("permite selecionar pelo explorador e remover via teclado", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn(),
      onRemove = vi.fn();
    const file = new File(["a"], "documento.pdf", { type: "application/pdf" });
    const { rerender } = render(
      <FileSelector
        file={null}
        disabled={false}
        maxSize={25}
        onSelect={onSelect}
        onRemove={onRemove}
      />,
    );
    await user.upload(screen.getByLabelText("Selecionar arquivo"), file);
    expect(onSelect).toHaveBeenCalledWith(file);
    rerender(
      <FileSelector
        file={file}
        disabled={false}
        maxSize={25}
        onSelect={onSelect}
        onRemove={onRemove}
      />,
    );
    screen.getByRole("button", { name: "Remover arquivo" }).focus();
    await user.keyboard("{Enter}");
    expect(onRemove).toHaveBeenCalledOnce();
  });
});

describe("Formatos e progresso honesto", () => {
  it("oferece somente saídas compatíveis", async () => {
    const onSelect = vi.fn();
    render(
      <OutputFormatSelector
        hasFile
        disabled={false}
        formats={["md"]}
        selected={null}
        onSelect={onSelect}
      />,
    );
    expect(screen.getAllByRole("button")).toHaveLength(1);
    await userEvent.click(screen.getByRole("button", { name: /Markdown/ }));
    expect(onSelect).toHaveBeenCalledWith("md");
  });
  it("não apresenta porcentagem precisa durante a conversão", () => {
    render(<ConversionProgress phase="processing" upload={100} />);
    expect(screen.getByRole("progressbar")).not.toHaveAttribute(
      "aria-valuenow",
    );
    expect(screen.getByText("EM ANDAMENTO")).toBeVisible();
    expect(screen.queryByText("100%")).not.toBeInTheDocument();
  });
  it("distingue o percentual de envio da conclusão", () => {
    const { rerender } = render(
      <ConversionProgress phase="uploading" upload={62} />,
    );
    expect(screen.getByRole("progressbar")).toHaveAttribute(
      "aria-valuenow",
      "62",
    );
    expect(
      screen.getByText("Percentual real do envio do arquivo."),
    ).toBeVisible();
    rerender(<ConversionProgress phase="success" upload={100} />);
    expect(screen.getByRole("progressbar")).toHaveAttribute(
      "aria-valuenow",
      "100",
    );
  });
  it("mostra erro dentro da tela e como texto, sem interpretar HTML", () => {
    const state = {
      phase: "error",
      file: null,
      input: "",
      output: null,
      result: null,
      error: "<script>conteudo()</script>",
      upload: 0,
      busy: false,
    } as ConverterState;
    const { container } = render(<ConversionScreen state={state} />);
    expect(screen.getByText("<script>conteudo()</script>")).toBeVisible();
    expect(container.querySelector("script")).toBeNull();
  });
});
