import { FileText, FileCode2, Table2, Presentation, Check } from "lucide-react";
import { FORMAT_NAMES, FORMAT_DETAILS, type OutputFormat } from "@/lib/config";
const icons = {
  md: FileCode2,
  docx: FileText,
  xlsx: Table2,
  pptx: Presentation,
};

export function OutputFormatSelector({
  formats,
  selected,
  disabled,
  hasFile,
  onSelect,
}: {
  formats: OutputFormat[];
  selected: OutputFormat | null;
  disabled: boolean;
  hasFile: boolean;
  onSelect: (format: OutputFormat) => void;
}) {
  const options = hasFile
    ? formats
    : (["md", "docx", "xlsx", "pptx"] as OutputFormat[]);
  return (
    <fieldset className="output-selector" disabled={disabled || !hasFile}>
      <legend className="field-label">
        <span>
          02 <b>CONVERTER PARA</b>
        </span>
        {selected && <span className="selected-output">.{selected}</span>}
      </legend>
      <div className="format-grid">
        {options.map((format) => {
          const Icon = icons[format];
          return (
            <button
              type="button"
              key={format}
              aria-pressed={selected === format}
              className={`format-button ${selected === format ? "selected" : ""}`}
              onClick={() => onSelect(format)}
            >
              <Icon size={20} strokeWidth={1.5} />
              <span>
                <strong>{FORMAT_NAMES[format]}</strong>
                <small>{FORMAT_DETAILS[format]}</small>
              </span>
              {selected === format ? (
                <Check className="format-check" size={13} />
              ) : (
                <em>.{format}</em>
              )}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
