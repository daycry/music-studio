import {expect, test} from '@playwright/test';

test('API-01 rechaza un Origin ajeno', async ({request}) => {
  const response = await request.post('http://127.0.0.1:8000/api/songs', {
    headers: {Origin: 'http://evil.test'},
    data: {title: 'No debe entrar', style_prompt: 'test'},
  });
  expect(response.status()).toBe(403);
  expect((await response.json()).code).toBe('FORBIDDEN_ORIGIN');
});

test('API-02 publica el contrato OpenAPI', async ({request}) => {
  const response = await request.get('http://127.0.0.1:8000/openapi.json');
  expect(response.status()).toBe(200);
  expect((await response.json()).paths['/api/generations']).toBeTruthy();
});
