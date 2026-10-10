# Validação da restauração — 10/10/2026

## Diagnóstico reproduzido

Base: `406f855a0c6c8837a90b61ec8ea1163210dc4469`, branch `main`.

- `python -m backend.worker`: módulo inexistente. Os oito testes originais falham sem o worker (`baseline-tests.txt`).
- API pública `https://the-convert-lab.onrender.com`: health/config/formats respondem, mas as sete conversões retornam 422 (`production-before.json`).
- Render: serviço `srv-db52832jnfac739019qg`, deploy antigo `dep-db5283ijnfac73901ba0`, marcado Live no commit acima. Esse estado não comprovava conversões.
- Frontend publicado: upload de PDF, seleção PowerPoint e erro de processamento reproduzido pelo navegador integrado.
- O relatório antigo mencionava 40 testes de backend, mas só oito estavam versionados. As evidências desta execução substituem essa afirmação.
- API não observava desconexão durante processamento; o sweeper podia parar numa corrida com remoção de pastas.
- Build estático do frontend gerava `out/index.html`, sem `.next/standalone/server.js`, contrariando o Dockerfile.

## Implementação

- `backend/worker.py`: valida diretório UUID sob TEMP_DIR, JSON limitado, formatos, arquivo regular, tamanho, MIME e estrutura; usa os motores existentes; reabre saída; publica status atômico. Exit 0 sucesso, 1 erro esperado, 2 falha interna. Remove saída parcial; detalhes internos não atravessam a API.
- `backend/api/routes.py`: valida contrato e exit code; preserva mensagens curadas; observa desconexão, timeout e cancelamento, incluindo a corrida durante criação do subprocesso; encerra processo antes da limpeza.
- `pdf_to_powerpoint.py`: evita extrair bytes de imagens desnecessariamente na análise de texto e identifica páginas com fallback visual nos avisos.
- `temporary_files.py`: tolera remoção simultânea durante a varredura.
- Testes: worker direto, corrupção, senha, ZIP/XML inseguro, limites, concorrência, cancelamento, timeout, falha de transmissão, HTTP/cabeçalhos/CORS e matriz real de formatos.
- Docker do frontend ativa standalone explicitamente. O padrão continua exportação estática para Netlify. Nenhum redesign nem alteração da variável da Netlify.
- `.gitignore`/`.dockerignore`: excluem ambientes, builds, caches e entradas/saídas locais. Bytecode e cache TypeScript removidos do versionamento.
- `.github/workflows/backend.yml`: build Docker e regressão sob restrições de produção em futuros pushes/PRs.
- Nenhuma dependência adicionada e nenhum limite ampliado.

## Testes executados

- Windows/Python 3.13.14: **61 aprovados, 0 reprovados, 0 ignorados** (`backend-tests.txt`).
- Linux/Python 3.13.16: **61 aprovados, 0 reprovados, 0 ignorados** (`backend-linux-tests.txt`).
- Interface: **8 aprovados, 0 reprovados, 0 ignorados** (`frontend-tests.txt`).
- Total final: **130 execuções aprovadas**. As oito falhas do baseline são anteriores à correção. Uma primeira coleta dos testes novos teve erro de nome reservado, corrigido antes das execuções finais.
- TypeScript e build estático Next.js passaram; `out/index.html` gerado.
- Imagens Docker de backend e frontend construídas; frontend inicia como usuário node e responde HTTP 200.
- Backend: UID 10001, filesystem read-only, `/tmp` tmpfs de 512 MB, memória 512 MB, 2 CPUs, 128 PIDs, sem capabilities e sem novos privilégios. `pip check` passou em Windows e Linux.
- Uvicorn e sete conversões HTTP reais no container passaram (`docker-http.json`); arquivos reabertos, valores/texto/slides, MIME, download, CORS e cabeçalhos conferidos.
- Pico de memória do container na matriz HTTP: **372.391.936 bytes (~355 MiB)** via cgroup `memory.peak`. `/tmp/convertlab` ficou sem subdiretórios de jobs ao final.
- `docker compose config --quiet` e `git diff --check` passaram.
- Aviso conhecido de depreciação do adaptador httpx do Starlette nos testes; não foram alteradas dependências para ocultá-lo.

## Matriz local e Docker

| Conversão | Resultado verificado |
|---|---|
| PDF → Markdown | Texto e tabela extraídos |
| DOCX → Markdown | Título, texto, negrito e tabela |
| PDF → DOCX | Reaberto com python-docx; texto e tabela presentes |
| PDF → XLSX | Reaberto com openpyxl; células e número 1250.5 |
| PDF → PPTX | Reaberto com python-pptx; texto editável e fallback visual |
| MHT → XLSX | MIME/HTML real; células tipadas; fórmula preservada como texto |
| MHTML → XLSX | Mesmo motor, upload independente validado |

PowerPoint: texto simples, multipágina, imagem, tabela/desenho, rotação e páginas com proporções diferentes. Slides contam as páginas, imagens permanecem dentro da área do slide, sem crop, e avisos identificam fallback. Não há promessa de editabilidade total nem fidelidade perfeita.

## Publicação e produção

A atualização deste bloco após o push registrará SHA, deploy observado e resultados posteriores. Até então, os testes públicos acima são o diagnóstico anterior à correção, não evidência de sucesso.

Comando reproduzível para validar as sete combinações:

```bash
python verification/smoke.py https://the-convert-lab.onrender.com verification/local/production
```

## Limitações

Entradas sintéticas, nunca substitutos dos resultados do produto. Sem OCR; PDFs digitalizados são recusados para Markdown/Excel e preservados visualmente em Word/PowerPoint. Documentos extremos podem atingir recursos/timeout. O pico de memória medido não caracteriza toda carga possível, especialmente duas conversões grandes simultâneas. Sem ensaio prolongado de carga, telefone físico ou abertura no Microsoft Office nativo.

O Render Free informa cold start de 50 segundos ou mais; a interface pode exigir Reconectar após seu timeout inicial. Upload via extensão Chrome ficou bloqueado por permissão de arquivos locais; o navegador integrado realizou o upload normalmente.
