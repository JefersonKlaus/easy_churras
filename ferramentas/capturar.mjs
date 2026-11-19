// Capturas de tela para as lojas, tiradas do app de verdade rodando no navegador.
//
//   npm install @sparticuz/chromium puppeteer-core
//   FLET_WEB_NO_CDN=true python ferramentas/servidor_capturas.py &
//   node ferramentas/capturar.mjs
//
// Grava em docs/screenshot/<loja>/NN-<tela>.png, no tamanho que cada loja pede.
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import chromium from '@sparticuz/chromium';
import puppeteer from 'puppeteer-core';

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..');
const ENDERECO = process.env.ENDERECO || 'http://127.0.0.1:8550';

// loja -> tela do aparelho (pontos) e densidade: o tamanho final é largura x altura x escala
const APARELHOS = {
  'android': { largura: 360, altura: 640, escala: 3 },      // 1080 x 1920 (Google Play, 9:16)
  'iphone-6.9': { largura: 430, altura: 932, escala: 3 },   // 1290 x 2796 (App Store)
  'ipad-13': { largura: 1024, altura: 1366, escala: 2 },    // 2048 x 2732 (App Store)
};

// na ordem em que aparecem na loja; `rolar` desce a lista antes da captura
const TELAS = [
  { nome: '01-inicio', rota: 'inicio' },
  { nome: '02-quem-vem', rota: 'quem' },
  { nome: '03-escolha', rota: 'escolha' },
  { nome: '04-carnes', rota: 'carnes' },
  { nome: '05-compras', rota: 'compras' },            // o açougue, com como pedir
  { nome: '06-horarios', rota: 'horarios', rolar: 420 },
];

const navegador = await puppeteer.launch({
  executablePath: await chromium.executablePath(),
  args: [...chromium.args, '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--lang=pt-BR'],
  headless: true,
});
for (const [loja, aparelho] of Object.entries(APARELHOS)) {
  const pasta = join(RAIZ, 'docs', 'screenshot', loja);
  mkdirSync(pasta, { recursive: true });
  for (const tela of TELAS) {
    const pagina = await navegador.newPage();
    // o Chromium sem interface não informa o idioma do jeito que o Flutter espera
    await pagina.evaluateOnNewDocument(() => {
      Object.defineProperty(navigator, 'language', { get: () => 'pt-BR' });
      Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt'] });
    });
    await pagina.setViewport({ width: aparelho.largura, height: aparelho.altura,
                               deviceScaleFactor: aparelho.escala });
    await pagina.goto(`${ENDERECO}/${tela.rota}`, { waitUntil: 'networkidle0', timeout: 90000 });
    await new Promise((r) => setTimeout(r, 8000));          // o Flutter desenhar a tela
    if (tela.rolar) {
      await pagina.mouse.move(aparelho.largura / 2, aparelho.altura / 2);
      await pagina.mouse.wheel({ deltaY: tela.rolar });
      await new Promise((r) => setTimeout(r, 1500));
    }
    const arquivo = join(pasta, `${tela.nome}.png`);
    await pagina.screenshot({ path: arquivo });
    console.log(arquivo);
    await pagina.close();
  }
}
await navegador.close();
