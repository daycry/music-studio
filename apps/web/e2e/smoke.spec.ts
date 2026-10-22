import {expect, test} from '@playwright/test';

test('abre el estudio y navega a Sistema', async ({page}) => {
  await page.goto('/create');
  await expect(page.getByRole('heading', {name: /crear/i})).toBeVisible();
  await page.getByRole('link', {name: /sistema/i}).click();
  await expect(page).toHaveURL(/\/system$/);
  await expect(page.getByRole('heading', {name: /sistema/i})).toBeVisible();
  const unload = page.getByRole('button', {name: /descargar modelo/i});
  await expect(unload).toBeEnabled();
  await unload.click();
  await expect(page.getByText(/modelo descargado/i)).toBeVisible();
});
