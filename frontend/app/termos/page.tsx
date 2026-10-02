import Link from "next/link";
export const metadata = { title: "Termos de uso" };
export default function Terms() {
  return (
    <main className="legal-page" id="conteudo">
      <Link className="back-link" href="/">
        ← Voltar ao conversor
      </Link>
      <span className="eyebrow">USO CONSCIENTE</span>
      <h1>Termos de uso</h1>
      <p className="legal-lead">Uma ferramenta simples, com limites claros.</p>
      <h2>Finalidade</h2>
      <p>
        O ConvertLab transforma arquivos entre os formatos apresentados na
        interface. O envio de um arquivo pressupõe que você está autorizado a
        processar seu conteúdo.
      </p>
      <h2>Qualidade dos resultados</h2>
      <p>
        A estrutura de um PDF nem sempre permite reconstrução perfeita. Revise
        documentos, tabelas e apresentações antes de utilizá-los. Fontes,
        imagens, células mescladas, fórmulas e layouts complexos podem
        apresentar diferenças. Os resultados não substituem o arquivo original.
      </p>
      <h2>Limites técnicos</h2>
      <p>
        O serviço aplica limites de tamanho, páginas, tempo e conversões
        simultâneas. Arquivos inválidos, protegidos por senha ou incompatíveis
        podem ser recusados. O reconhecimento óptico de caracteres ainda não
        está disponível.
      </p>
      <h2>Uso permitido</h2>
      <p>
        Não envie arquivos maliciosos, tente acessar documentos de outras
        pessoas ou use automação para sobrecarregar o serviço. O conteúdo dos
        documentos não é executado pelo ConvertLab.
      </p>
      <h2>Disponibilidade e privacidade</h2>
      <p>
        O serviço depende da disponibilidade do servidor de conversão. Arquivos
        não são mantidos como cópia de segurança. Consulte a{" "}
        <Link href="/privacidade">Política de Privacidade</Link> para entender o
        processamento e a exclusão dos arquivos temporários.
      </p>
    </main>
  );
}
