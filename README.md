# ConvertLab

Aplicação de conversão real de documentos com uma interface de dois módulos: monitor de conversão à esquerda e controles à direita. No celular, os controles aparecem primeiro. Identidade própria em vermelho profundo, telas grafite, indicador de estado e dobradiça construída com CSS; sem imagens ou elementos de franquias.

## Começar

Pré-requisitos: **Python 3.13**, **Node.js 24** e **pnpm 10.30.3**. Não é necessário banco de dados, login, chave de API ou serviço de IA.

### Backend

Na raiz deste projeto:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

macOS / Linux:

```bash
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

### Frontend

Em outro terminal:

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Abra **http://127.0.0.1:3000**. A API está em **http://127.0.0.1:8000** e sua documentação em **http://127.0.0.1:8000/docs**.

O frontend usa o backend local por padrão. Para alterar, copie `frontend/.env.example` para `frontend/.env.local` e configure a URL. Os limites exibidos são lidos da API. Se a API estiver desligada, o upload fica desativado e aparece a ação **Reconectar**.

### Docker

Com o serviço Docker ativo, na raiz do projeto:

```bash
docker compose up --build
```

Depois do primeiro build, `docker compose up` é suficiente. Abra http://localhost:3000. As portas são publicadas apenas na interface local. Para outra origem, ajuste `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL` e `CORS_ORIGINS` antes do build.

Os containers executam sem root. O backend tem filesystem somente leitura, temporários em `tmpfs`, limite de memória, CPU e processos. Não há volume de documentos persistente. O serviço Docker não estava ativo no ambiente da entrega; a sintaxe do Compose foi validada, mas o build Linux e a execução dos containers ainda precisam ser realizados.

## Conversões

| Entrada | Saída | Estratégia |
| --- | --- | --- |
| PDF | Markdown | PyMuPDF4LLM: hierarquia, texto, tabelas, imagens incorporadas quando extraídas |
| DOCX | Markdown | Mammoth → HTML interno → Markdown; títulos, listas, links, ênfase e tabelas |
| PDF | Word | pdf2docx; fallback com texto editável e imagens das páginas |
| PDF | Excel | Detecção por linhas; tentativa por alinhamento de texto quando necessário |
| PDF | PowerPoint | Texto simples como objetos editáveis; layouts complexos como imagem de página |
| MHT / MHTML | Excel | MIME → HTML principal → tabelas → células tipadas e formatadas |

Todas as saídas são reabertas/validadas no servidor antes de serem enviadas. Não há mudança artificial de extensão, conversão simulada ou resposta de exemplo no fluxo principal. Os arquivos sintéticos dos testes servem exclusivamente para verificação.

### Comportamento da interface

- Seleção pelo explorador ou drag and drop de um arquivo por vez.
- Detecção automática da extensão; opções válidas vêm de `GET /api/formats`.
- Percentual real **apenas no envio**. Durante a conversão, barra indeterminada e estado textual. `100%` de conversão somente depois da resposta válida.
- Download com nome original sanitizado e extensão de saída.
- Markdown: baixar, copiar, visualizar ou inspecionar código. A prévia é carregada sob demanda, não executa HTML e não busca imagens externas.
- Prévia limitada a 5 MB; downloads Markdown maiores continuam disponíveis.
- Modo claro/escuro: detecta preferência do sistema na primeira visita; escolha manual persiste localmente.
- Indicador circular e LEDs refletem estados reais; todos os controles têm função.
- Teclado, foco visível, região de anúncio de estado, fechamento de prévia por Escape e respeito a movimento reduzido.

## Arquitetura

```text
convertlab/
  frontend/
    app/                   # Home, privacidade, termos, 404, SEO e CSS
    components/device/     # Dois painéis, indicadores, upload, saídas e download
    components/            # Navegação, tema e prévia Markdown
    hooks/use-converter.ts # Máquina de estados, ciclo de vida de arquivos e requisições
    services/api.ts         # Contrato HTTP, envio XHR e download Blob
    lib/config.ts          # Nome do produto, formatos e helpers
    tests/                 # Drag and drop, teclado, opções e progresso
    Dockerfile
  backend/
    main.py                # FastAPI, CORS, limite de corpo e limpeza periódica
    config.py              # Variáveis e matriz de formatos
    api/routes.py          # Upload, processos isolados e resposta temporária
    worker.py              # Validação → conversão → validação de saída
    converters/
      registry.py          # Registro de módulos independentes
      pdf/                 # Markdown, Word, Excel e PowerPoint
      docx/                # Markdown
      mht/                 # Excel para MHT e MHTML
    services/              # Assinaturas, MIME, temporários, tabelas e layouts
    tests/                 # Testes reais de arquivos e segurança
    Dockerfile
  verification/            # Evidências e relatório da validação
  compose.yaml
  .env.example
```

Cada conversão roda em um **subprocesso independente** com timeout. Isso evita compartilhar o estado interno dos motores PDF entre threads e permite terminar uma conversão travada. O backend mantém limite de concorrência por processo; excesso recebe HTTP 429. Em produção, use um worker Uvicorn por container ou ajuste os limites considerando que múltiplos workers multiplicam a concorrência.

Adicionar uma conversão exige um módulo `convert(source: Path, target: Path) -> list[str]`, uma entrada em `registry.py`, a matriz em `config.py`, validação de entrada/saída e testes. O retorno contém somente avisos curados, nunca conteúdo do documento. Novos tipos de saída também precisam de rótulos e ícones no frontend. A separação permite evoluir para filas, lotes e OCR sem misturar UI e motores; esses recursos futuros não estão implementados.

## API

### `POST /api/convert`

`multipart/form-data` com `file` e `output_format`. Responde com o arquivo final e `Content-Disposition`. O cabeçalho `X-Conversion-Warnings` contém uma lista JSON codificada com percent-encoding, usada para informar fallbacks. `Cache-Control: no-store` impede cache do resultado.

```bash
curl -F "file=@relatorio.pdf" -F "output_format=md" http://127.0.0.1:8000/api/convert --output relatorio.md
```

| Código | Significado |
| --- | --- |
| 200 | Arquivo convertido e validado |
| 400 | Formato/combinação inválida |
| 413 | Limite de tamanho ultrapassado |
| 422 | Conteúdo inválido, senha, ausência de tabelas/texto ou processamento inviável |
| 429 | Capacidade ocupada |
| 504 | Tempo de processamento excedido |

`GET /api/formats` retorna a matriz solicitada. `GET /api/config` expõe limites públicos. `GET /api/health` permite healthcheck. Não há endpoint público para listar ou recuperar arquivos de outra conversão.

## Configuração

| Variável | Padrão | Local |
| --- | --- | --- |
| `MAX_FILE_SIZE_MB` | `25` | Backend |
| `MAX_PDF_PAGES` | `150` | Backend |
| `CONVERSION_TIMEOUT_SECONDS` | `120` | Backend |
| `MAX_CONCURRENT_CONVERSIONS` | `2` | Backend, por worker |
| `TEMP_DIR` | diretório temporário do SO + `/convertlab` | Backend |
| `CORS_ORIGINS` | localhost e 127.0.0.1, porta 3000 | Backend; origens separadas por vírgula |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Frontend, no build |
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3000` | Frontend, no build |

O backend lê variáveis do processo; ele **não carrega `.env` automaticamente**. No desenvolvimento, exporte-as no terminal. O Docker Compose lê o `.env` da raiz para interpolação. Exemplo PowerShell: `$env:MAX_FILE_SIZE_MB = '25'` antes de iniciar a API.

## Segurança e privacidade implementadas

- Limites no corpo HTTP e no arquivo, incluindo corpo sem `Content-Length`.
- MIME compatível **e** assinatura/estrutura: PDF real, ZIP DOCX validado e multipart MIME para MHT.
- Arquivos DOCX com partes muito grandes, macros, caminhos inseguros ou XML inseguro são recusados; limite de expansão ZIP de 150 MB.
- Nomes UUID usados somente internamente. Nomes originais nunca viram caminhos de armazenamento.
- Acesso a arquivos externos desabilitado no conversor Word; o parser MHT não navega nem busca recursos.
- Dados de planilha são gravados como texto quando não são números/datas, impedindo fórmulas vindas do documento.
- Limite de resultado de 150 MB e de 500 mil células tabulares; limites também para spans de tabelas HTML.
- Temporários removidos após transmissão, erro ou timeout. Pastas órfãs com mais de uma hora são limpas na inicialização e a cada dez minutos.
- Registros técnicos sem nomes e sem conteúdo. Saída de bibliotecas de conversão não vai para logs HTTP.
- Documentos não são enviados a provedores de IA; nenhum LLM participa do processamento.

O processo isolado não é um sandbox completo do sistema operacional. O container limita recursos; uma instalação pública ainda deve usar HTTPS, regras de acesso e limitação de requisições no provedor/reverse proxy. CORS não é autenticação. Não execute o backend público como administrador/root.

## Testes e build

Na raiz, com o ambiente Python ativado:

```bash
python -m pytest -q
```

No diretório `frontend`:

```bash
pnpm test
pnpm typecheck
pnpm build
pnpm start
```

Os testes Python produzem PDFs, Word e MIME sintéticos, passam pela API, reabrem DOCX/XLSX/PPTX e conferem conteúdo. Incluem tabelas, datas, percentuais, zeros à esquerda, fórmulas maliciosas, arquivos corrompidos, senha, scans, ZIP excessivo, timeout, concorrência e limpeza. Testes React cobrem drag and drop, seleção pelo explorador, remoção por teclado, formatos compatíveis e progresso honesto.

O relatório em `verification/VALIDACAO.md` distingue o que foi executado de limitações de ambiente. Abrir as saídas no Microsoft Office real não foi validado; elas foram reabertas por bibliotecas dos formatos.

## Deploy

### Vercel — frontend

Importe o projeto e selecione `frontend` como Root Directory. Build: `pnpm build`. Configure `NEXT_PUBLIC_API_URL` com a URL HTTPS pública da API e `NEXT_PUBLIC_SITE_URL` com a URL pública do frontend. As variáveis públicas são incorporadas no build, então alterações exigem novo deploy.

O navegador envia o upload **diretamente à API Python**. A conversão não usa Vercel Functions nem passa por uma função com limite de corpo menor que 25 MB.

### Backend Python

Use uma plataforma com suporte a container ou processo Python persistente. O Dockerfile está em `backend/Dockerfile`, com contexto de build na raiz. Configure `CORS_ORIGINS` para a origem exata da Vercel e healthcheck `/api/health`. Garanta suporte a requisições longas, subprocessos, diretório temporário e memória para os motores. A porta padrão é 8000; adapte o comando caso o provedor exija `PORT`.

Nenhum deploy externo foi realizado nesta entrega.

## Limitações conhecidas

- OCR não implementado. Markdown/Excel recusam páginas detectadas como digitalizadas; Word/PowerPoint preservam essas páginas como imagens.
- Detecção de scans é heurística e não identifica todos os PDFs com texto como contornos vetoriais.
- PDF não contém necessariamente semântica de títulos, listas ou tabelas. Cabeçalhos repetidos e layouts incomuns podem exigir revisão.
- Tabelas sem bordas podem ser reconhecidas de forma imperfeita. Cada tabela detectada ganha uma aba; não há recomposição automática entre páginas.
- Números ambíguos como `1.234`, identificadores longos e zeros à esquerda permanecem texto para evitar alterações silenciosas. Células mescladas HTML ocupam a grade com conteúdo na primeira célula; fórmulas e mesclagem visual não são recriadas.
- PowerPoint com imagens, desenhos, rotação ou layout complexo usa fallback visual por página. Texto simples usa fonte de substituição Arial; não há reconstrução editável de todos os layouts.
- Word pode usar fallback de texto e imagens, com aparência simplificada e possível duplicação visual do texto nas imagens de referência.
- Sem lotes, ZIP de resultados, autenticação, histórico, integração com nuvem ou OCR avançado nesta versão.
- `backend/requirements.txt` congela o ambiente de validação Python. A instalação nativa foi validada em Windows/Python 3.13; o build Linux ainda precisa ser executado com Docker ativo.

## Referências dos motores

- [PyMuPDF4LLM — API e parâmetros](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html)
- [PyMuPDF — extração de tabelas e páginas](https://pymupdf.readthedocs.io/en/latest/page.html)
- [FastAPI — respostas e tarefas após envio](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Next.js — instalação](https://nextjs.org/docs/app/getting-started/installation)

PyMuPDF/PyMuPDF4LLM usam licenciamento AGPL/comercial. A escolha dessa dependência está documentada; consulte os [termos do fornecedor](https://pymupdf.io/licensing) antes de distribuir ou operar uma versão proprietária. Este projeto não declara uma licença própria em nome do usuário.
