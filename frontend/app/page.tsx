import {
  ArrowDownUp,
  ArrowRight,
  FileCheck2,
  Fingerprint,
  LockKeyhole,
  Upload,
  MousePointer2,
  Download,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { ConverterDevice } from "@/components/device/converter-device";

export default function Home() {
  return (
    <main id="conteudo">
      <section className="hero">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="tiny-line" /> MENOS LIMITES. MAIS FORMATOS.
          </div>
          <h1>
            Seus arquivos.<span> Novas possibilidades.</span>
          </h1>
          <p>Transforme documentos. Preserve o que importa.</p>
        </div>
        <ConverterDevice />
        <div className="trust-strip">
          <span>
            <LockKeyhole size={15} /> Privacidade por padrão
          </span>
          <span>
            <Zap size={15} /> Sem cadastro. Sem complicação.
          </span>
          <span>
            <FileCheck2 size={15} /> Conversões reais, arquivos válidos
          </span>
        </div>
      </section>
      <section className="content-section formats-section" id="formatos">
        <div className="section-intro">
          <span className="eyebrow">01 / COMPATIBILIDADE</span>
          <h2>
            O arquivo certo.
            <br />
            <span>No formato que você precisa.</span>
          </h2>
          <p>
            De documentos a dados estruturados, um lugar para transformar seu
            trabalho.
          </p>
        </div>
        <div className="format-table">
          <div className="format-table-head">
            <span>SEU ARQUIVO</span>
            <span>SUAS POSSIBILIDADES</span>
          </div>
          {[
            ["PDF", ["Markdown", "Word", "Excel", "PowerPoint"]],
            ["DOCX", ["Markdown"]],
            ["MHT / MHTML", ["Excel"]],
          ].map(([input, outputs]) => (
            <div className="format-table-row" key={input as string}>
              <strong>
                <ArrowDownUp size={16} />
                {input}
              </strong>
              <div>
                {(outputs as string[]).map((output) => (
                  <span key={output}>{output}</span>
                ))}
              </div>
            </div>
          ))}
          <p>
            Excel extrai tabelas. PDFs complexos podem gerar slides como
            imagens.
          </p>
        </div>
      </section>
      <section className="content-section how-section" id="como-funciona">
        <div className="section-heading">
          <div>
            <span className="eyebrow">02 / SEM COMPLICAÇÃO</span>
            <h2>Do upload ao próximo passo.</h2>
          </div>
          <p>Quatro passos. Nenhuma conta.</p>
        </div>
        <div className="steps">
          {[
            {
              Icon: Upload,
              title: "Envie",
              text: "Arraste um documento ou selecione no seu dispositivo.",
            },
            {
              Icon: MousePointer2,
              title: "Escolha",
              text: "Veja os formatos compatíveis e escolha a saída.",
            },
            {
              Icon: ArrowDownUp,
              title: "Converta",
              text: "Acompanhe o envio e o estado do processamento.",
            },
            {
              Icon: Download,
              title: "Baixe",
              text: "Seu novo arquivo está pronto para o que vem a seguir.",
            },
          ].map(({ Icon, title, text }, index) => (
            <div className="step" key={title}>
              <div>
                <Icon size={22} strokeWidth={1.5} />
                <span>0{index + 1}</span>
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="privacy-section">
        <div className="privacy-symbol">
          <Fingerprint size={48} strokeWidth={1.1} />
        </div>
        <div>
          <span className="eyebrow">SEU CONTEÚDO CONTINUA SENDO SEU.</span>
          <h2>Privacidade faz parte do processo.</h2>
          <p>
            Seus documentos são usados apenas para a conversão. Sem histórico,
            sem conta e sem armazenamento permanente.
          </p>
        </div>
        <Link href="/privacidade">
          Conheça a política <ArrowRight size={16} />
        </Link>
      </section>
      <section className="content-section faq-section">
        <div className="section-intro">
          <span className="eyebrow">03 / BOM SABER</span>
          <h2>Antes de converter.</h2>
          <p>Respostas diretas para seguir em frente.</p>
        </div>
        <div className="faq-list">
          {[
            [
              "O layout do meu arquivo será preservado?",
              "Preservamos conteúdo e estrutura sempre que possível. Word prioriza edição; Excel extrai tabelas; PowerPoint mantém a aparência, usando imagens para páginas complexas. A interface informa quando um fallback é utilizado.",
            ],
            [
              "Posso converter um PDF digitalizado?",
              "Você pode gerar um PowerPoint ou um Word com imagens das páginas. Para Markdown e Excel, é necessária uma camada de texto. O reconhecimento de texto (OCR) ainda não está disponível.",
            ],
            [
              "O que acontece com os arquivos enviados?",
              "Os arquivos temporários são removidos após o envio do resultado ao navegador, inclusive em erros tratados. Restos de processos interrompidos são limpos automaticamente após uma hora, com verificação a cada dez minutos.",
            ],
            [
              "Existe um limite de tamanho?",
              "A configuração inicial é de 25 MB por arquivo e 150 páginas por PDF. O limite de tamanho vigente aparece na área de upload. Documentos muito complexos podem atingir o limite de processamento.",
            ],
          ].map(([q, a]) => (
            <details key={q}>
              <summary>
                {q}
                <span>+</span>
              </summary>
              <p>{a}</p>
            </details>
          ))}
        </div>
      </section>
    </main>
  );
}
