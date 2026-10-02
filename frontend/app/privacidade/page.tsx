import Link from "next/link";
export const metadata = { title: "Privacidade" };
export default function Privacy() {
  return (
    <main className="legal-page" id="conteudo">
      <Link className="back-link" href="/">
        ← Voltar ao conversor
      </Link>
      <span className="eyebrow">TRANSPARÊNCIA POR PADRÃO</span>
      <h1>Política de Privacidade</h1>
      <p className="legal-lead">
        Seu arquivo tem um destino: o formato que você escolheu.
      </p>
      <h2>Processamento temporário</h2>
      <p>
        O ConvertLab recebe o documento no servidor configurado para realizar a
        conversão. O arquivo de entrada e o resultado ficam em uma pasta
        temporária isolada, identificada por um código aleatório. Não há conta,
        banco de dados ou histórico de documentos.
      </p>
      <h2>Exclusão dos arquivos</h2>
      <p>
        A pasta temporária é removida depois que o resultado é transmitido ao
        navegador. Erros tratados também acionam a limpeza. Em caso de
        interrupção abrupta do servidor, pastas com mais de uma hora são
        removidas na inicialização e em verificações a cada dez minutos.
      </p>
      <h2>Registros técnicos</h2>
      <p>
        Os registros da aplicação podem conter formato, tamanho, duração, estado
        e categoria técnica de erro. O conteúdo dos documentos e seus nomes
        originais não são incluídos nesses registros. O provedor de hospedagem
        pode manter registros de acesso conforme sua configuração.
      </p>
      <h2>No seu navegador</h2>
      <p>
        O resultado permanece na memória do navegador para permitir download,
        cópia ou visualização e é liberado ao remover o arquivo, iniciar outra
        conversão ou fechar a página. Somente a preferência de tema é salva
        localmente. A prévia Markdown não busca imagens remotas.
      </p>
      <h2>Serviços e processamento</h2>
      <p>
        As conversões utilizam bibliotecas de processamento de documentos no
        servidor, sem envio para serviços de IA generativa. Esta aplicação não
        inclui ferramentas de publicidade ou análise de comportamento.
      </p>
      <h2>Antes de usar</h2>
      <p>
        Envie somente documentos que você tem autorização para processar. Em uma
        instalação própria, a configuração de hospedagem, transporte HTTPS e
        acesso aos registros é responsabilidade de seu operador.
      </p>
    </main>
  );
}
