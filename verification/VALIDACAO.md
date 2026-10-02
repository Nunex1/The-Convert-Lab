# Validação — ConvertLab

Data: 2 de outubro de 2026. Ambiente: Windows, Python 3.13.14, Node.js 24.19.0.

## Resultado

**Implementação local funcional.** Sete combinações de conversão implementadas; arquivos reais produzidos e reabertos. **40 testes de backend e 8 testes de interface aprovados.** TypeScript sem erros e build de produção Next.js concluído.

## Backend

Evidência: `backend-tests.txt`.

- PDF → Markdown: título e tabela conferidos no texto.
- DOCX → Markdown: título, negrito e tabela conferidos.
- MHT e MHTML → Excel: moeda, percentual e data reabertos como tipos adequados.
- PDF → Word: texto e dados da tabela reabertos com python-docx.
- PDF → Excel: `Receita` e `1250.5` encontrados nas células esperadas.
- PDF → PowerPoint: slide com fallback visual confirmado; cenário separado verifica texto editável.
- Arquivos inválidos, vazios e formatos incompatíveis recusados.
- MIME incorreto, assinatura incorreta, ZIP excessivo e senha recusados.
- Limites de arquivo, corpo HTTP com e sem Content-Length, timeout e concorrência verificados.
- Scan recusado para Markdown/Excel e convertido em Word com imagem da página.
- Ausência de tabelas resulta em mensagem objetiva.
- Fórmulas de planilha permanecem texto. Zeros à esquerda e números ambíguos não são convertidos silenciosamente.
- Temporários limpos após sucesso, erro, timeout e falha na transmissão da resposta; limpeza de órfãos respeita pastas recentes.

Há um aviso de depreciação do adaptador httpx do TestClient/Starlette; ele não impediu os testes nem afeta o fluxo de produção. A dependência está congelada para reprodução.

## Interface

Evidência: `frontend-tests.txt`.

- Drag and drop recebe um arquivo, informa limite de seleção múltipla e impede substituição durante processamento.
- Seleção pelo input de arquivo e remoção usando Enter.
- Apenas saídas compatíveis ficam disponíveis após seleção.
- Percentual exibido no envio; conversão sem percentual inventado.
- Erros exibidos como texto, sem interpretar HTML recebido.

## Navegador com API real

- Seleção de PDF; escolha Markdown; estado real de processamento; sucesso; prévia renderizada; aba Código; fechamento por Escape.
- Download Markdown confirmado no disco: contém título e tabela da amostra.
- Ação Copiar retornou sucesso na interface. O adaptador de clipboard do navegador não expôs o conteúdo na releitura; colagem em outro aplicativo não foi validada.
- DOCX → Markdown concluído na disposição mobile.
- MHT → Excel concluído e baixado.
- PDF → Word, Excel e PowerPoint concluídos e baixados. Os três downloads foram reabertos diretamente do disco com bibliotecas de seus formatos.
- Avisos de fallback do Word/PowerPoint apresentados na interface.
- PDF com conteúdo inválido apresentou erro inline com a causa, sem modal.
- Tema claro e escuro alternados.
- Desktop 1440 × 1000, tablet 820 × 1180, mobile 390 × 844 e largura mínima 320 px sem overflow horizontal. Tablet manteve painéis lado a lado; mobile colocou controles acima do monitor.
- Nenhum aviso/erro de console retornado na inspeção final do navegador.

Capturas:

- `desktop-dark.png`: versão desktop em modo escuro.
- `tablet-light.png`: tablet em modo claro.
- `mobile-dark.png`: disposição vertical completa.
- `mobile-error.png`: erro de PDF inválido no monitor.

## Compilação e infraestrutura

- `pnpm typecheck`: passou.
- `pnpm build`: passou; rotas `/`, `/privacidade`, `/termos`, 404, robots e sitemap geradas.
- Servidor standalone de produção iniciado localmente. Home, privacidade, termos, robots e sitemap responderam HTTP 200; caminho inexistente retornou 404. API respondeu ao healthcheck e a uma nova conversão PDF → Markdown com HTTP 200 e `Cache-Control: no-store`.
- `docker compose config --quiet`: passou.
- Dockerfiles e Compose preparados; daemon Docker indisponível, portanto **build e execução Linux não verificados**.
- Deploy externo não realizado.

## Limites da validação

As amostras sintéticas verificam os mecanismos, não garantem fidelidade em todos os documentos. Não houve abertura no Microsoft Word/Excel/PowerPoint nativos, teste em telefone físico, ensaio de carga ou pentest. OCR não está implementado. As limitações e fallbacks estão descritos no README e na interface. Não foram utilizados mocks nas conversões da aplicação.
