import Link from "next/link";
export default function NotFound() {
  return (
    <main className="not-found" id="conteudo">
      <span className="eyebrow">ERRO / 404</span>
      <h1>Este caminho não tem saída.</h1>
      <p>Mas seus arquivos têm várias. Volte ao conversor para começar.</p>
      <Link className="primary-button" href="/">
        Voltar ao ConvertLab →
      </Link>
    </main>
  );
}
