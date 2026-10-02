import type { Metadata } from "next";
import { DM_Sans, IBM_Plex_Mono } from "next/font/google";
import { Navbar, Footer } from "@/components/navigation";
import "./globals.css";
const sans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});
const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

const description =
  "Converta PDF, Word e MHT em Markdown, documentos, planilhas e apresentações. Sem cadastro e sem armazenamento permanente.";
export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
  ),
  title: {
    default: "ConvertLab — Novas possibilidades para seus arquivos",
    template: "%s | ConvertLab",
  },
  description,
  openGraph: {
    title: "ConvertLab — Seu próximo formato começa aqui",
    description,
    type: "website",
    locale: "pt_BR",
  },
  icons: { icon: "/icon.svg" },
};
const themeScript = `(function(){try{var t=localStorage.getItem('convertlab-theme');document.documentElement.dataset.theme=t||(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark')}catch(e){document.documentElement.dataset.theme='dark'}})()`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="pt-BR"
      className={`${sans.variable} ${mono.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body>
        <a className="skip-link" href="#conteudo">
          Pular para o conteúdo
        </a>
        <Navbar />
        {children}
        <Footer />
      </body>
    </html>
  );
}
