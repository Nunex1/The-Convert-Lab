# Evolução de planilhas e desempenho — 14/10/2026

## A. Diagnóstico e planejamento

Base remota conferida por fetch: `a7b5d6c13094a78a7994ba0ed58037149d0c7947`. Árvore inicialmente limpa; branch `codex/spreadsheet-performance`. Foram lidos AGENTS.md e o guia use-client incluído no Next.js instalado, 16.3.8.

O registro já fazia importação tardia. Porém, file_validator carregava PyMuPDF inclusive para DOCX/MHT. Agora o import ocorre somente no ramo PDF, preservando validações. Upload limitado, FileResponse, subprocesso por trabalho, timeout e limpeza já existiam e foram mantidos. Downloads continuam usando Blob no navegador, com consumo de memória correspondente; não se implementou streaming direto para disco.

| Decisão | Impacto | Complexidade/risco | Resultado |
| --- | --- | --- | --- |
| Importação tardia de PyMuPDF | Menos RAM/importação fora de PDF | Baixos | Mantida após medição |
| CSV incremental | Evita materializar tabela inteira | Médios: tipos/caches/escape | Implementado e verificado até 100 mil linhas |
| Inspeção OOXML incremental | Segurança e limites | Médios: falsos positivos | Implementada; proteção vazia corrigida |
| XLSB comercial opcional | Escrita binária/fórmulas | Licença e dependências nativas | Bloqueado sem licença |
| Pool persistente | Potencial ganho em arquivos pequenos | Alto: cancelamento, memória, crash | Apenas experimento, fora da API |
| CSS por estados | Feedback imediato | Baixos | Implementado e verificado |

Não foram introduzidos banco, filas externas, SSE/polling ou keep-alive.

## B. Alterações e arquivos

- `backend/services/file_validator.py`: PyMuPDF tardio e encaminhamento XLSX.
- `backend/services/spreadsheet_validator.py`: ZIP/XML incremental; rejeita duplicatas, caminhos inseguros, partes criptografadas, macros, conexões, referências externas, fórmulas com comandos/serviços externos e coordenadas fora dos limites do Excel. Limites: 150 MB expandidos, 100 MB por parte, razão ZIP 1000, 16 MB de shared strings/estilos, cinco milhões de células, profundidade XML 100. Não extrai arquivos; DTD/entidades proibidos. Proteção ativa rejeitada, tag workbookProtection vazia aceita.
- `backend/services/csv_options.py`, `backend/converters/xlsx/xlsx_to_csv.py`: opções leves no processo HTTP, leitura read-only, escrita por linha, fechamento garantido.
- `backend/converters/xlsx/xlsx_to_xlsb.py`, `backend/services/capabilities.py`: licença validada; prova de escrita/reabertura em subprocesso limitado a 30 s; cache por inicialização. Falha mantém XLSB ausente. Cada trabalho verifica licença novamente. Compara nomes/ordem das abas e percorre saída com pyxlsb antes do download.
- `backend/worker.py`, `backend/api/routes.py`: opções multipart opcionais e Server-Timing por etapa, sem conteúdo ou nomes de documentos nos tempos/logs.
- Config, registro, detector e validador de resultado: novos formatos/MIME/validações; contratos antigos preservados.
- `backend/main.py`: prova opcional de capacidade no startup, fora do event loop.
- `backend/requirements-xlsb.txt`, `backend/Dockerfile.xlsb`: dependências comerciais separadas da instalação padrão.
- Config/API/hook do frontend: formatos, opções no mesmo upload e proteção de callbacks de operações canceladas; espera inicial limitada a 90 s para cold start.
- Componentes de seleção, monitor, painel, `csv-options.tsx`, CSS e página inicial: controles, explicações, animação e opções dinâmicas no fluxo.
- Testes backend/frontend e scripts em verification: evidências abaixo.

## C. Novas conversões

### CSV operacional

POST /api/convert aceita output_format=csv e JSON opcional em csv_options:

```json
{"delimiter":";","bom":false,"sheet":"Dados","protect_formulas":true}
```

Padrão: ponto e vírgula, UTF-8 sem BOM, primeira worksheet, proteção ativa. Aba escolhida por nome exato antes do único upload; lista automática de abas não implementada. Resultado identifica aba exportada e quantidade omitida. Nome inexistente é erro, sem fallback silencioso.

csv.writer trata delimitadores, aspas e quebras de linha. Booleanos são TRUE/FALSE; datas ISO 8601; decimais com ponto; durações em segundos. Texto 00123 e máscaras simples 00000 são preservados. Excel pode reinterpretar códigos: importar essas colunas como texto. CSV não preserva estilos arbitrários, gráficos ou mesclagens.

Fórmulas não são executadas: exporta-se o cache salvo; sem cache, célula vazia, informado antes/depois. Textos potencialmente executáveis recebem apóstrofo, com contagem no aviso. Usuário pode escolher texto literal explicitamente. Números negativos reais continuam numéricos. Validação final percorre CSV inteiro com UTF-8 estrito e delimitador escolhido.

Read-only não garante memória constante para todo arquivo: openpyxl carrega shared strings/estilos, portanto há limites próprios. A proteção conservadora rejeita hyperlinks externos também.

### XLSB condicionado

Requer pacote opcional, ENABLE_XLSB=1, ASPOSE_CELLS_LICENSE_PATH e prova de startup aprovada. Sem isso, API anuncia xlsx:[csv] e recusa XLSB. Licença deve ser segredo montado, nunca commitada ou incluída na imagem.

Aspose.Cells 26.9.0 foi instalado em Windows/Python 3.13 e Linux x86_64/Python 3.13.16. Wheels: 59,2 MB Windows e 88,7 MB Linux. Linux precisou de ICU, libgdiplus/fontconfig, CLR_ICU_VERSION_OVERRIDE=76 e cache de fontes em /tmp. Somente pip não bastou.

Prova Linux em 512 MB/read-only/tmpfs (`linux-xlsb-probe.json`): workbook.bin presente, workbook.xml ausente; pyxlsb recuperou Unicode, número, booleano e zeros; reabertura Aspose confirmou fórmula simples. Uma prova pequena levou 0,906 s e gerou 6.799 bytes. Não é benchmark representativo. A avaliação acrescentou uma terceira aba às duas originais: inaceitável para produção. Arquivo excluído automaticamente, nunca entregue pela API.

Teste licenciado existe e foi pulado. Fidelidade comercial de estilos avançados, pivôs, gráficos, datas e XLSB grandes permanece pendente. Integração preparada não significa ativação aprovada.

| Motor | XLSB | Linux/fidelidade | Custo/tamanho |
| --- | --- | --- | --- |
| Aspose via .NET | Escrita comprovada | Python 3.13.16 testado; fórmula simples preservada | Comercial, wheel Linux 88,7 MB mais SO |
| SheetJS CE | Escreve binário | Requer Node; matriz oficial não marca escrita de fórmulas XLSB como suportada | Open source; não instalado/medido aqui; não atende preservação de fórmulas exigida |
| openpyxl/XlsxWriter | Não escrevem XLSB | Python/Linux; openpyxl já instalado | CSV sem nova dependência |
| pyxlsb | Somente leitura | Verificador independente, não garante todos os estilos | Wheel ~23 KB |
| LibreOffice | Escrita não comprovada nas opções oficiais consultadas | Não adotado como escritor sem suporte demonstrado | Não instalado/medido |

Fontes: [formatos SheetJS](https://docs.sheetjs.com/docs/miscellany/formats/), [fórmulas SheetJS](https://docs.sheetjs.com/docs/csf/features/formulae/), [Aspose instalação](https://docs.aspose.com/cells/python-net/getting-started/), [Docker/ICU](https://docs.aspose.com/cells/net/how-to-run-aspose-cells-python-via-net-in-docker/), [avaliação/licença](https://docs.aspose.com/cells/python-net/licensing/), [LibreOffice](https://help.libreoffice.org/latest/en-US/text/shared/guide/ms_user.html).

[Preços Aspose](https://purchase.aspose.com/pricing/): Cells a partir de US$ 1.199. Preço inicial publicado, não cotação da licença para este SaaS público: distribuição, desenvolvedores e modalidade exigem confirmação comercial. Nada comprado.

## D. Experiência visual

Idle estável; selected com entrada breve; uploading com pulsos e percentual XHR real; processing com varredura indeterminada; receiving inverte varredura e mostra saída; success confirma arquivo validado; error interrompe e permite tentar novamente. Opções CSV recolhíveis evitam painel muito alto. CSS transform/opacity, sem biblioteca nova, com movimento reduzido e região de anúncio preservados.

Playwright/Edge headless executou aba, upload, conversão, download e comparação de CSV em 1440×1100 e 390×844 (movimento reduzido). Sem erros JS ou overflow horizontal. Capturas inspecionadas visualmente. Clique→sucesso: 0,888 s desktop / 1,399 s mobile; duas observações, não benchmark de dispositivos reais.

## E. Desempenho

Dez execuções de baseline e cinco da revisão final por caso em Linux, 512 MB/1 CPU. Base extraída com git archive a7b5d6c; mesmos fixtures, dependências e medidor. P95 nearest-rank (nessas amostras pequenas: máximo). RSS é pico amostrado incluindo descendentes; intervalo mínimo de 5 ms mais custo do medidor. Host WSL compartilhado teve outras tarefas; não é SLA ou isolamento físico de CPU.

| Caso | Antes mediana/p95 (s) | Depois mediana/p95 (s) | RSS antes→depois MiB | Redução mediana | Saída |
| --- | --- | --- | --- | --- | --- |
| Importação worker | 0,949 / 1,160 | 0,416 / 0,465 | 56,84→21,16 | 56,1% | — |
| DOCX→MD, 100 parágrafos | 1,539 / 2,032 | 1,288 / 1,424 | 83,00→51,86 | 16,3% | 5.089 B |
| PDF→PPTX, uma página | 1,095 / 3,542 | 0,994 / 1,113 | 79,09→78,73 | 9,2% | 28.365 B |
| XLSX→CSV, 100 linhas | indisponível | 1,092 / 1,122 | —→49,54 | nova função | 4.480 B |
| XLSX→CSV, 10 mil linhas | indisponível | 3,400 / 3,884 | —→51,11 | nova função | 487.780 B |
| XLSX→CSV, 100 mil linhas | indisponível | 25,291 / 26,221 | —→66,29 | nova função | 5.077.780 B |

Brutos: linux-performance-before/after.json. Seis células por linha XLSX. Ensaio intermediário com dez execuções preservado em linux-performance-initial.json; resultado DOCX intermediário foi 27,2%, mas a tabela usa a revisão final, com as validações de coordenadas/fórmulas externas. Benchmark inicial CSV incluía import de openpyxl em conversion; código final contabiliza em converter_import.

Controle alternado Windows (`paired-performance.json`, dez pares): importação 0,323→0,161 s; DOCX 1,149→1,024 s (10,9%); RSS DOCX 71,00→46,86 MiB. P95 DOCX piorou 1,938→3,755 s. Windows não pareado, preservado em performance-*.json, sofreu carga simultânea e não é evidência de ganho. Meta de 30% na conversão completa não comprovada. Ganhos de memória e medianas justificam import tardio.

HTTP local (`http-performance.json`), cinco POSTs sequenciais: mediana total 612 ms; health inicial 9,76 ms; upload ~0,38–0,52 ms; recebimento ~0,16–0,20 ms. Server-Timing discrimina capacidade, cópia, worker, imports, validações e conversão. Primeiro POST: import do conversor 435,53 ms, leitura/conversão 6,36 ms, validação entrada 5,61 ms, resultado 2,40 ms. Código final acrescenta spawn separado; evidências iniciais precedem esse campo. Interpretador puro: ~25–30 ms, medido à parte.

Leitura/escrita incremental está agregada à execução do conversor; não há atribuição fictícia de disco versus transformação. Em 100 mil linhas: inspeção XML mediana 6,94 s, importação do conversor 0,54 s, conversão 16,89 s e validação final 0,21 s. Validações mantidas por segurança.

Duas consultas manuais à API pública: HTTP 200, primeira 22,803 s/TCP 36 ms; posterior 0,230 s/TCP 21 ms. Compatível com inicialização, mas não prova cold start sem confirmação de suspensão no painel. Config pública confirmou 25 MB, 150 páginas e timeout 120 s. Sem upload de documentos em produção ou requisições periódicas.

Pool experimental, dez DOCX (`pool-performance.json`): primeiro 1,348 s; nove aquecidos, mediana 0,326 s/p95 0,381 s; residência após tarefas 56–67 MiB. Não implementa cancelamento forte, descarte de memória ou recuperação de falha nativa: mantido fora da API. Demonstra potencial, não segurança equivalente.

Dois conversores/HTTP 429 preservados e testados. Não há carga sustentada/adversa suficiente no plano real para aumentar concorrência. Ensaio 512 MB não prova que dois documentos nos limites máximos caibam simultaneamente. XLSB grande exige medição licenciada.

## F. Testes

- Baseline: 61 backend + 8 frontend aprovados.
- Windows final: **110 passaram, um pulado por licença**, `backend-spreadsheets-regression.txt`; inclui conversões anteriores, timeout/cancelamento/desconexão, concorrência, headers, limpeza, segurança e BOM em aba vazia.
- Linux sem opcionais: 98 passaram/2 pulados (`linux-spreadsheets-tests.txt`).
- Linux com motor opcional, revisão de segurança incluída: **109 passaram, um pulado por licença** (`linux-xlsb-regression.txt`). Refinamento de BOM em aba vazia verificado separadamente em dois casos (`linux-empty-csv-tests.txt`).
- Três testes compararam todas as células de 100/10.000/100.000 linhas, também registrados isoladamente em `linux-large-csv-tests.txt` e incluídos na suíte final.
- Frontend: 14 testes, TypeScript e build aprovados.
- Navegador: dois fluxos completos; JSON e PNGs em verification.
- XLSB: formato autêntico de avaliação comprovado; produção bloqueada, round trip comercial pendente.

Correções encontradas: tag de proteção vazia rejeitada; id pytest excessivo da fixture ZIP; ICU/fontconfig/Skia ausentes; indexação de worksheets na prova Aspose. Permanece aviso preexistente Starlette/httpx.

## G. Infraestrutura e reprodução

Netlify/Render e planos preservados. Evidência anterior do projeto menciona Free, mas plano atual não autenticado neste trabalho. [Render Free](https://render.com/docs/free) suspende após 15 min e pode levar cerca de um minuto para iniciar. Espera inicial do cliente passou de 10 para 90 s com mensagem; não elimina cold start nem mantém servidor artificialmente ativo.

Alternativas dentro do Render: Free (US$ 0, suspensão); compute pago 0,5 CPU/512 MB (US$ 7/mês, remove suspensão); mais recursos conforme [preços](https://render.com/pricing) e [compute plans](https://render.com/docs/compute-plans). Valores sem impostos/excedentes/licença. Nenhum upgrade/migração feito.

```sh
python -m pytest -q
# em frontend:
node node_modules/vitest/vitest.mjs run
node node_modules/typescript/bin/tsc --noEmit
node node_modules/next/dist/bin/next build
# raiz:
python -m verification.benchmark --output verification/performance-after.json --xlsx
python -m verification.paired_benchmark
docker build -f backend/Dockerfile -t convertlab-backend:latest .
docker build -f backend/Dockerfile.xlsb -t convertlab-xlsb-test .
```

Windows usa .venv/Scripts/python.exe. Benchmark pareado exige baseline extraída em verification/local/baseline. Segundo Dockerfile é opcional e não habilita XLSB. Montar licença read-only, configurar variáveis e executar teste licenciado em staging antes de ativação. Instalação nativa Render exige dependências do SO; pip sozinho não basta.

Docker: --memory 512m --cpus 1 --read-only --tmpfs /tmp:rw,size=256m, usuário converter, sem capabilities adicionais. Reavaliar tmpfs/CPU/RAM total para arquivos maiores.

## H. Entrega e pendências

Branch codex/spreadsheet-performance, commits separados por backend, frontend e documentação/validação, Pull Request para revisão. Sem merge ou publicação. CSV implementado; XLSB condicionado à licença. Fidelidade licenciada, carga sustentada no plano real e cold start controlado permanecem pendentes, não declarados concluídos.
