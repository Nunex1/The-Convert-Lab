// PLAYWRIGHT_MODULE may point to the bundled Playwright package on desktop.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}) });
  const observations = [];
  try {
    for (const [name, width, height, motion] of [['desktop', 1440, 1100, 'no-preference'], ['mobile', 390, 844, 'reduce']]) {
      const page = await browser.newPage({ viewport: { width, height }, reducedMotion: motion, colorScheme: 'dark' });
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto('http://127.0.0.1:3000');
      const upload = page.getByLabel('Selecionar arquivo');
      await page.getByText('ONLINE', { exact: true }).waitFor();
      await upload.setInputFiles(path.resolve('verification/local/browser.xlsx'));
      await page.getByText('Ajustar aba, separador e segurança').click();
      await page.getByLabel('Nome exato da aba (opcional)').fill('Dados');
      await page.getByText('Ajustar aba, separador e segurança').click();
      if (await page.getByRole('button', { name: /Excel binário/ }).count()) throw new Error('Unavailable XLSB visible');
      await page.screenshot({ path: `verification/xlsx-${name}-selected.png`, fullPage: true });
      const before = performance.now();
      await page.getByRole('button', { name: 'Converter arquivo', exact: true }).click();
      await page.getByText('Conversão concluída', { exact: true }).waitFor({ timeout: 120000 });
      const elapsed = performance.now() - before;
      const download = await Promise.all([
        page.waitForEvent('download'),
        page.getByRole('link', { name: /Baixar/ }).click(),
      ]).then(([download]) => download);
      const downloadPath = await download.path();
      const contents = fs.readFileSync(downloadPath, 'utf8');
      if (!contents.includes('Ação, teste;12.5;00123')) throw new Error('CSV content mismatch');
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (overflow || errors.length) throw new Error(JSON.stringify({ overflow, errors }));
      await page.screenshot({ path: `verification/xlsx-${name}-success.png`, fullPage: true });
      observations.push({ name, width, height, motion, elapsed_ms: elapsed, download: download.suggestedFilename(), overflow, errors });
      await page.close();
    }
    fs.writeFileSync('verification/browser-spreadsheets.json', JSON.stringify(observations, null, 2));
    console.log(JSON.stringify(observations, null, 2));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
