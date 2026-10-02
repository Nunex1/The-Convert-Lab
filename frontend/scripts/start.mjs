import { access, cp, mkdir } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const root = new URL('../', import.meta.url);
const standalone = new URL('.next/standalone/', root);

try {
  await access(new URL('server.js', standalone));
} catch {
  console.error('Execute pnpm build antes de iniciar o servidor de produção.');
  process.exit(1);
}

// Next standalone intentionally excludes assets; include them for local serving.
await mkdir(new URL('.next/', standalone), { recursive: true });
await cp(new URL('.next/static/', root), new URL('.next/static/', standalone), { recursive: true });
await cp(new URL('public/', root), new URL('public/', standalone), { recursive: true });
process.env.HOSTNAME ||= '0.0.0.0';
process.env.PORT ||= '3000';
process.chdir(fileURLToPath(standalone));
await import(new URL('server.js', standalone).href);
