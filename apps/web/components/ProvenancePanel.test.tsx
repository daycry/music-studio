// @vitest-environment jsdom
import React from 'react';
import {render, screen, fireEvent} from '@testing-library/react';
import {expect, test, vi} from 'vitest';
import {NextIntlClientProvider} from 'next-intl';
import messages from '../messages/es.json';
import {ProvenancePanel} from './ProvenancePanel';

test('permite copiar hashes y exportar la procedencia', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, {clipboard: {writeText}});
  render(<NextIntlClientProvider locale="es" messages={messages}><ProvenancePanel take={{id:'take-1', song_id:'song-1', model_id:'mock', task:'music.song', seed:7, params:{}, status:'ready', rating:null, favorite:false, label:'A', error_code:null, assets:{listen:{url:'/audio', media_type:'audio/mpeg', sha256:'abc123'}}} as never}/></NextIntlClientProvider>);
  expect(screen.getByRole('link', {name: messages.songDetail.exportProvenance})).toBeTruthy();
  fireEvent.click(screen.getAllByRole('button', {name: messages.songDetail.copy})[1]);
  expect(writeText).toHaveBeenCalledWith('abc123');
});
