import Link from "next/link";
import { ArrowDownUp } from "lucide-react";
import { BRAND } from "@/lib/config";
import { ThemeToggle } from "./theme-toggle";

export function Navbar() {
  return (
    <header className="navbar">
      <Link className="brand" href="/" aria-label={`${BRAND}, início`}>
        <span className="brand-mark">
          <ArrowDownUp size={18} strokeWidth={2.4} />
        </span>
        {BRAND}
        <span className="brand-period">.</span>
      </Link>
      <nav aria-label="Navegação principal">
        <Link className="nav-converters" href="/#formatos">
          Conversores
        </Link>
        <Link href="/privacidade">Privacidade</Link>
        <span className="nav-divider" />
        <ThemeToggle />
      </nav>
    </header>
  );
}
export function Footer() {
  return (
    <footer className="footer">
      <Link className="footer-brand" href="/">
        {BRAND}
        <span>.</span>
      </Link>
      <p>Uma nova forma para as suas ideias.</p>
      <div>
        <Link href="/privacidade">Privacidade</Link>
        <Link href="/termos">Termos de uso</Link>
      </div>
      <span className="copyright">
        © {new Date().getFullYear()} {BRAND}
      </span>
    </footer>
  );
}
