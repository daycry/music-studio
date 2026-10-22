import {expect, test} from '@playwright/test';

test('E2E-09 muestra BPM y beats de un análisis terminado', async ({page}) => {
  const songId = '01K70000000000000000000021';
  const takeId = '01K70000000000000000000022';
  await page.route('http://127.0.0.1:8000/api/session/bootstrap', route => route.fulfill({json: {session_token: 'analysis-session'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}`, route => route.fulfill({json: {id:songId, title:'Libre', artist:null, status:'ready', style_prompt:'hip hop', master_take_id:takeId, updated_at:'2026-01-01T00:00:00Z', created_at:'2026-01-01T00:00:00Z'}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/takes`, route => route.fulfill({json:{items:[{id:takeId, song_id:songId, status:'ready', task:'music.song', model_id:'mock', seed:1, params:{}, duration_s:4, rating:null, favorite:false, label:'A', error_code:null, assets:{listen:{url:'/api/takes/audio', media_type:'audio/mpeg', sha256:'a'}}}]}}));
  await page.route(`http://127.0.0.1:8000/api/songs/${songId}/lyrics`, route => route.fulfill({json:{items:[]}}));
  await page.route(`http://127.0.0.1:8000/api/takes/${takeId}/peaks`, route => route.fulfill({json:{data:[[[.2,.4,.6]]]}}));
  await page.route(`http://127.0.0.1:8000/api/takes/${takeId}/analysis`, route => route.fulfill({json:{items:[{id:'analysis-1',kind:'audio.beats',data:{bpm:120,beats_s:[0,.5,1,1.5]}}]}}));
  await page.goto(`/songs/${songId}`);
  await expect(page.getByText('BPM: 120')).toBeVisible();
  await expect(page.locator('.waveform [role="slider"]')).toBeVisible();
});
