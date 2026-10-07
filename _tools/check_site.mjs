// check_site.mjs -- automated "Test before deploying" checks (CMSC 601 slide 34) for riishavguptaa.com.
// Where it sits: run locally before every push; drives your installed Google Chrome, nothing is published.
// Input:  argv[2] = page to test (default: ../index.html as a file:// URL; or https://riishavguptaa.com/)
//         argv[3] = folder for screenshots (default: a temp folder)
// Output: a printed report -- horizontal overflow per screen width, accessibility violations (axe-core),
//         keyboard Tab order with focus visibility, status of every link, meta/preview tags -- plus screenshots.
// Run:    cd _tools && npm install && node check_site.mjs

import puppeteer from 'puppeteer-core';                                  // [L] puppeteer-core, not puppeteer: drives the Chrome you already have, no 150 MB download
import fs from 'node:fs';                                                // [L] fs/path/os/url: Node built-ins for files and temp folders
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const here = path.dirname(fileURLToPath(import.meta.url));               // [L] this script's folder, so paths work from anywhere
const require = createRequire(import.meta.url);                          // [L] require.resolve finds axe-core's file inside node_modules
const AXE_PATH = require.resolve('axe-core/axe.min.js');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const TARGET = process.argv[2] || pathToFileURL(path.resolve(here, '..', 'index.html')).href;
const OUT = process.argv[3] || fs.mkdtempSync(path.join(os.tmpdir(), 'site-check-'));
fs.mkdirSync(OUT, { recursive: true });                                  // [L] create the screenshot folder if it's new; recursive: no error if it already exists
const WIDTHS = [1440, 1024, 768, 390, 375, 320];                         // [L] desktop, laptop, tablet, iPhone 14, iPhone SE; 320 px = a 1280 px window at 400% zoom (WCAG reflow test)

/** Open TARGET at a given viewport and wait for fonts, so measurements match what visitors see.
 *  page: puppeteer Page; width/height: CSS px; dpr: device pixel ratio (2 = Retina / 200% zoom).
 *  Method: networkidle0 waits until no network requests for 500 ms (Google Fonts, icons, images). */
async function open(page, width, height, dpr = 1) {
  const mobile = width <= 480;                                           // [L] <= 480 px treated as a phone: touch events, mobile viewport rules
  await page.setViewport({ width, height, deviceScaleFactor: dpr, isMobile: mobile, hasTouch: mobile });
  await page.goto(TARGET, { waitUntil: 'networkidle0', timeout: 60000 });  // [L] 60 s: generous for slow CDNs
  await page.evaluate(() => document.fonts.ready);                       // [L] web fonts change text width; measure only after they load
}

/** Return {scroll, inner, offenders}: page width vs window width, and elements sticking out on the right. */
async function overflow(page) {
  return page.evaluate(() => {
    const inner = window.innerWidth;
    const offenders = [];
    for (const el of document.querySelectorAll('body *')) {              // [L] every element, to name the culprit if the page overflows
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.right > inner + 1) {                          // [L] +1 px tolerance for sub-pixel rounding
        offenders.push(`${el.tagName.toLowerCase()}${el.className ? '.' + String(el.className).split(' ')[0] : ''} (right edge ${Math.round(r.right)} px)`);
      }
    }
    return { scroll: document.documentElement.scrollWidth, inner, offenders: offenders.slice(0, 5) };
  });
}

async function main() {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--no-first-run'] });
  const page = await browser.newPage();
  console.log(`Testing ${TARGET}\nScreenshots -> ${OUT}\n`);

  // Check 1: narrow screens and zoom (slide 25: "test narrow screens, zoom, long titles")
  console.log('== 1. Layout: horizontal overflow at each width ==');
  const layouts = [...WIDTHS.map((w) => [w, w <= 480 ? 844 : 900, 1, `${w}px`]), [640, 450, 2, '200% zoom (1280px window)']];
  for (const [w, h, dpr, label] of layouts) {
    await open(page, w, h, dpr);
    const o = await overflow(page);
    const ok = o.scroll <= o.inner;                                      // [L] page no wider than the window = no sideways scrolling
    console.log(`  ${ok ? 'PASS' : 'FAIL'}  ${label.padEnd(26)} page ${o.scroll}px / window ${o.inner}px${ok ? '' : '  offenders: ' + o.offenders.join('; ')}`);
    await page.screenshot({ path: path.join(OUT, `layout-${label.replace(/[^0-9a-z]+/gi, '_')}.png`), fullPage: true });
  }

  // Check 2: accessibility checker (slides 26, 34) -- axe-core with every <details> opened so hidden text is checked too
  console.log('\n== 2. Accessibility (axe-core, WCAG 2.2 A/AA + best practices) ==');
  for (const w of [1280, 375]) {                                         // [L] desktop and phone layouts can fail differently (e.g. contrast over different backgrounds)
    await open(page, w, 900);
    await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
    await page.addScriptTag({ path: AXE_PATH });
    const res = await page.evaluate(async () => axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] },
    }));
    console.log(`  ${w}px: ${res.violations.length} violations, ${res.passes.length} rules passed, ${res.incomplete.length} need a human look`);
    for (const v of res.violations) {
      console.log(`    - [${v.impact}] ${v.id}: ${v.help} (${v.nodes.length}x, e.g. ${v.nodes[0].target.join(' ')})`);
    }
    for (const v of res.incomplete) console.log(`    ? ${v.id}: ${v.help} (${v.nodes.length}x)`);
  }

  // Check 3: keyboard -- Tab through every interactive element (slide 34); each must show a focus ring
  console.log('\n== 3. Keyboard: Tab order and visible focus ==');
  await open(page, 1280, 800);
  const seen = [];
  for (let i = 0; i < 120; i++) {                                        // [L] 120 presses: more than the page has, so we see it wrap around
    await page.keyboard.press('Tab');
    const f = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      const cs = getComputedStyle(el);
      return {
        label: (el.innerText || el.getAttribute('aria-label') || el.tagName).trim().replace(/\s+/g, ' ').slice(0, 48),
        tag: el.tagName.toLowerCase(),
        ring: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0,   // [L] a visible outline = the focus ring is drawn
      };
    });
    if (!f || (seen.length && f.label === seen[0].label && f.tag === seen[0].tag)) break;  // [L] back at the start = full cycle done
    seen.push(f);
  }
  const noRing = seen.filter((f) => !f.ring);
  console.log(`  ${seen.length} focusable elements reached; first = "${seen[0]?.label}"; without a visible ring: ${noRing.length}`);
  console.log('  order: ' + seen.map((f) => f.label).join(' | '));
  for (const f of noRing) console.log(`    no ring: <${f.tag}> "${f.label}"`);

  // Check 4: click every important link (slide 34) -- in-page anchors, local files, and external URLs
  console.log('\n== 4. Links ==');
  await open(page, 1280, 800);
  const refs = await page.evaluate(() => [
    ...[...document.querySelectorAll('a[href]')].map((a) => ({ kind: 'link', url: a.href, text: a.innerText.trim().slice(0, 40) })),
    ...[...document.querySelectorAll('img[src], link[href]')].map((e) => ({ kind: e.tagName.toLowerCase(), url: e.src || e.href, text: '' })),
    ...[...document.querySelectorAll('[srcset]')].flatMap((e) => e.srcset.split(',').map((s) => ({ kind: 'srcset', url: new URL(s.trim().split(' ')[0], location.href).href, text: '' }))),
  ]);
  const ids = new Set(await page.evaluate(() => [...document.querySelectorAll('[id]')].map((e) => e.id)));
  const unique = [...new Map(refs.map((r) => [r.url, r])).values()];   // [L] check each URL once, even if linked several times
  const results = await Promise.all(unique.map(async (r) => {
    const u = new URL(r.url);
    if (u.protocol === 'mailto:') return { ...r, status: 'mailto' };
    if (u.protocol === 'file:') {
      if (u.hash && u.pathname.endsWith('index.html')) return { ...r, status: ids.has(u.hash.slice(1)) ? 'ok (anchor)' : 'MISSING ANCHOR' };
      return { ...r, status: fs.existsSync(decodeURIComponent(u.pathname)) ? 'ok (file)' : 'MISSING FILE' };
    }
    try {
      const res = await fetch(r.url, { redirect: 'follow', signal: AbortSignal.timeout(20000),   // [L] 20 s per link, then give up
        headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36' } });
      return { ...r, status: res.status };
    } catch (e) { return { ...r, status: 'ERROR ' + (e.cause?.code || e.name) }; }
  }));
  for (const r of results) {
    const ok = r.status === 'mailto' || String(r.status).startsWith('ok') || (r.status >= 200 && r.status < 400);
    console.log(`  ${ok ? 'PASS' : 'CHECK'}  ${String(r.status).padEnd(13)} ${r.url}${r.text ? '  "' + r.text + '"' : ''}`);
  }

  // Check 5: title, icons, social/search preview (slide 34)
  console.log('\n== 5. Title, icons, preview tags ==');
  const meta = await page.evaluate(() => {
    const q = (s) => document.querySelector(s)?.getAttribute('content') || document.querySelector(s)?.getAttribute('href') || null;
    let ld = 'missing';
    try { const j = JSON.parse(document.querySelector('script[type="application/ld+json"]').textContent); ld = `${j['@type']}: ${j.name} / ${j.alternateName}`; } catch (e) { ld = 'INVALID JSON-LD'; }
    return {
      title: document.title, description: q('meta[name="description"]'), canonical: q('link[rel="canonical"]'),
      'og:title': q('meta[property="og:title"]'), 'og:image': q('meta[property="og:image"]'), 'og:image:alt': q('meta[property="og:image:alt"]'),
      'twitter:card': q('meta[name="twitter:card"]'), icon: q('link[rel="icon"]'), 'apple-touch-icon': q('link[rel="apple-touch-icon"]'), 'json-ld': ld,
      h1: [...document.querySelectorAll('h1')].map((h) => h.textContent.trim()),
    };
  });
  for (const [k, v] of Object.entries(meta)) console.log(`  ${v ? 'PASS' : 'MISSING'}  ${k}: ${Array.isArray(v) ? v.join(', ') : v}`);

  await browser.close();
}

main().catch((e) => { console.error(e); process.exit(1); });
