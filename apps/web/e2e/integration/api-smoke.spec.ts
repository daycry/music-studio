import {expect, test} from '@playwright/test';
import {apiOrigin} from './helpers';

test('API-01 rechaza un Origin ajeno por HTTP real', async ({request}) => {
  const response = await request.post(`${apiOrigin}/api/songs`, {
    headers: {Origin: 'http://evil.test'},
    data: {title: 'No debe entrar', style_prompt: 'test'},
  });
  expect(response.status()).toBe(403);
  expect((await response.json()).code).toBe('FORBIDDEN_ORIGIN');
});

test('API-01 rechaza un Host ajeno por HTTP real', async ({request}) => {
  const response = await request.get(`${apiOrigin}/health`, {headers: {Host: 'evil.test'}});
  expect(response.status()).toBe(403);
  expect((await response.json()).code).toBe('INVALID_HOST');
});

test('API-02 publica OpenAPI y la operación de generación por HTTP real', async ({request}) => {
  const response = await request.get(`${apiOrigin}/openapi.json`);
  expect(response.status()).toBe(200);
  const contract = await response.json();
  expect(contract.paths['/api/generations'].post).toBeTruthy();
});
