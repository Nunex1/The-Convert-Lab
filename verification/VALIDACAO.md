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

- Correção publicada em `main`, sem force push: [`bd523489972b50fb7f94edd04746e7a1c79a97c9`](https://github.com/Nunex1/The-Convert-Lab/commit/bd523489972b50fb7f94edd04746e7a1c79a97c9). A base remota foi reconferida imediatamente antes do commit/push e não havia alterações concorrentes.
- GitHub Actions [38053980109](https://github.com/Nunex1/The-Convert-Lab/actions/runs/38053980109): **success**, build Docker e regressão aprovados (`github-ci.json`).
- Render, serviço `srv-db52832jnfac739019qg`, [deploy dep-db53d7k9v7es738n3fg0](https://dashboard.render.com/web/srv-db52832jnfac739019qg/deploys/dep-db53d7k9v7es738n3fg0): **Deploy succeeded | Live**, source `bd52348`, Auto-Deploy, duração 32,7 segundos. Painel indica 10/10/2026 09:59:11 GMT-3; logs registram Live às 09:59:43. Build sem falhas; Uvicorn iniciou como processo 1 na porta 8000, aplicação inicializada, WEB_CONCURRENCY=1.
- API: `https://the-convert-lab.onrender.com`. Health, formatos e configuração responderam corretamente. **Sete conversões com HTTP 200 e conteúdo reaberto/validado**, com MIME, nome de download, avisos, CORS e cabeçalhos corretos (`production-after.json`). Duração observada: 6,93–35,55 segundos nesta matriz.
- Site: `https://theconvertlab.netlify.app/`. **Sete conversões completas pelo navegador integrado**, com upload pelo seletor, processamento real, estado de sucesso e download. Todos os arquivos baixados foram reabertos/verificados no disco; hashes e tamanhos em `browser-downloads.json`.
- PPTX baixado pelo site: 41.335 bytes, dois slides; texto `ConvertLab validation` editável no primeiro, imagem da tabela no segundo. O aviso identificou a página 2 e sua limitação de editabilidade.
- DOCX/Markdown/Excel do site também tiveram conteúdo conferido. O Word preservou texto, o Markdown de DOCX preservou negrito e as planilhas contêm `Revenue` e 1250.5.
- Desktop e viewport móvel 390 × 844 verificados; largura do conteúdo 375 px, sem overflow horizontal. Capturas: `production-pptx-success.jpg` e `production-mobile-pptx.jpg`.
- PDF inválido enviado pelo site retornou a mensagem segura: “O arquivo não possui uma assinatura PDF válida.” A interface saiu do processamento e não ofereceu falso download.
- Nenhum erro de CORS ou HTTP inesperado nos fluxos bem-sucedidos. O console do frontend já existente registrou React #418 na carga inicial (também antes do deploy). Esse aviso de hidratação não foi reproduzido no container local e não bloqueou nenhuma das sete conversões; sua causa não foi confirmada. Não foi feita alteração especulativa na UI para ocultá-lo.

Comando reproduzível para validar as sete combinações:

```bash
python verification/smoke.py https://the-convert-lab.onrender.com verification/local/production
```

## Limitações

Entradas sintéticas, nunca substitutos dos resultados do produto. Sem OCR; PDFs digitalizados são recusados para Markdown/Excel e preservados visualmente em Word/PowerPoint. Documentos extremos podem atingir recursos/timeout. O pico de memória medido não caracteriza toda carga possível, especialmente duas conversões grandes simultâneas. Sem ensaio prolongado de carga, telefone físico ou abertura no Microsoft Office nativo.

O Render Free informa cold start de 50 segundos ou mais; a interface pode exigir Reconectar após seu timeout inicial. Upload via extensão Chrome ficou bloqueado por permissão de arquivos locais; o navegador integrado realizou o upload normalmente.

**CORREÇÃO CONCLUÍDA E VALIDADA EM PRODUÇÃO**, com as limitações amostrais e o aviso preexistente de hidratação descritos acima.
