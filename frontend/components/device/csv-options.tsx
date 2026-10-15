import type { CsvOptions as Options } from "@/services/api";

export function CsvOptions({ value, onChange, disabled }: {
  value: Options; onChange: (value: Options) => void; disabled: boolean;
}) {
  return <fieldset className="csv-options" disabled={disabled}>
    <legend>Exportar uma aba</legend>
    <p>CSV contém uma única tabela. Deixe o nome vazio para exportar a primeira aba; as demais não serão incluídas.</p>
    <details>
    <summary>Ajustar aba, separador e segurança</summary>
    <label>Nome exato da aba (opcional)
      <input maxLength={31} value={value.sheet} placeholder="Primeira aba" onChange={e => onChange({ ...value, sheet: e.target.value })} />
    </label>
    <label>Separador
      <select value={value.delimiter} onChange={e => onChange({ ...value, delimiter: e.target.value as Options["delimiter"] })}>
        <option value=";">Ponto e vírgula (;)</option><option value=",">Vírgula (,)</option>
      </select>
    </label>
    <label className="csv-check"><input type="checkbox" checked={value.bom} onChange={e => onChange({ ...value, bom: e.target.checked })} /> BOM para Excel</label>
    <label className="csv-check"><input type="checkbox" checked={value.protect_formulas} onChange={e => onChange({ ...value, protect_formulas: e.target.checked })} /> Proteger textos que possam executar fórmulas</label>
    <p>{value.protect_formulas ? "Textos suspeitos recebem um apóstrofo inicial; essa alteração será informada no resultado." : "Atenção: textos serão preservados literalmente. Importe como texto para evitar execução de fórmulas."}</p>
    </details>
    <p>Fórmulas usam os valores calculados salvos; sem valor salvo, ficam vazias. Estilos e mesclagens não são preservados. Datas em ISO e decimais com ponto.</p>
  </fieldset>;
}
