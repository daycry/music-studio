import {expect, test} from '@playwright/test';
import {observeBrowserSessions, revokeSessions} from './helpers';

test.beforeEach(async ({page}) => observeBrowserSessions(page));
test.afterEach(async ({page, request}, testInfo) => revokeSessions(page, request, testInfo));

for (const width of [1440, 768, 390]) {
  test(`biblioteca layout legible y contenido a ${width}px`, async ({page}, testInfo) => {
    await page.setViewportSize({width, height: 1000});
    await page.goto('/songs');
    await expect(page.locator('.song-card').nth(1), 'Biblioteca privada de prueba ya poblada').toBeVisible();
    for (const [mode, label] of [['grid', 'Cuadrícula'], ['list', 'Lista']] as const) {
      await page.getByRole('button', {name: label, exact: true}).click();
      await expect(page.locator('.song-library')).toHaveClass(new RegExp(`\\b${mode}\\b`));
      await page.evaluate(() => document.fonts.ready);
      const geometry = await page.locator('.song-card').evaluateAll(cards => {
        const rect = (element: Element) => {
          const {left, top, right, bottom, width, height} = element.getBoundingClientRect();
          return {left, top, right, bottom, width, height};
        };
        return cards.map(card => {
          const body = card.querySelector('.song-card-body')!;
          const title = body.querySelector('h2')!;
          const style = getComputedStyle(title);
          return {card: rect(card), body: rect(body), title: rect(title), titleText: title.textContent,
            titleOverflow: {client: title.clientWidth, scroll: title.scrollWidth, overflow: style.overflow, ellipsis: style.textOverflow},
            parts: Array.from(card.children).map(rect), controls: Array.from(card.querySelectorAll('button, select')).map(rect)};
        });
      });
      await testInfo.attach(`library-${mode}-${width}-geometry`, {body: JSON.stringify(geometry, null, 2), contentType: 'application/json'});
      const violations: string[] = [];
      const overlaps = (a: typeof geometry[number]['card'], b: typeof geometry[number]['card']) =>
        Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1;
      geometry.forEach((item, index) => {
        if (item.body.width < 80 || item.title.width < 80 || !item.titleText?.trim()) violations.push(`card ${index}: cuerpo/título ilegible (${item.body.width}/${item.title.width}px)`);
        if (item.titleOverflow.scroll > item.titleOverflow.client + 1 && (item.titleOverflow.overflow !== 'hidden' || item.titleOverflow.ellipsis !== 'ellipsis')) violations.push(`card ${index}: título largo sin elipsis`);
        for (const part of [...item.parts, ...item.controls]) {
          if (part.left < item.card.left - 1 || part.right > item.card.right + 1 || part.top < item.card.top - 1 || part.bottom > item.card.bottom + 1) violations.push(`card ${index}: contenido fuera de tarjeta`);
        }
        item.parts.forEach((part, i) => item.parts.slice(i + 1).forEach(other => {if (overlaps(part, other)) violations.push(`card ${index}: bloques solapados`);}));
        geometry.slice(index + 1).forEach(other => {if (overlaps(item.card, other.card)) violations.push(`card ${index}: tarjetas solapadas`);});
      });
      const viewport = await page.evaluate(() => ({scroll: document.documentElement.scrollWidth, client: document.documentElement.clientWidth}));
      expect.soft(viewport.scroll, `${mode}: sin desplazamiento horizontal de página`).toBeLessThanOrEqual(viewport.client + 1);
      expect.soft(violations, `${mode}: texto y controles legibles dentro de cada tarjeta`).toEqual([]);
      await page.screenshot({path: testInfo.outputPath(`library-${mode}-${width}.png`), fullPage: true});
    }
  });
}
