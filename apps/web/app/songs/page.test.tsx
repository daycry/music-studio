// @vitest-environment jsdom
import React from 'react';
import {act, cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {NextIntlClientProvider} from 'next-intl';
import {afterEach, beforeEach, expect, test, vi} from 'vitest';
import messages from '../../messages/es.json';
import {deleteSong, listSongTrash, moveSong, purgeSong, restoreSong, listSongs} from '../../lib/api';
import SongsPage from './page';
vi.mock('../../lib/api', async original => ({...await original<typeof import('../../lib/api')>(), listSongs: vi.fn(), deleteSong: vi.fn(), listSongTrash: vi.fn(), moveSong: vi.fn(), purgeSong: vi.fn(), restoreSong: vi.fn()}));
vi.mock('../../components/CollectionsPanel', () => ({CollectionsPanel: ({onSelect, onLoaded}: {onSelect: (id: string) => void; onLoaded: (items: never) => void}) => <><button onClick={() => onLoaded([{id: 'collection-a', name: 'Album'}] as never)}>Cargar colecciones</button><button onClick={() => onSelect('collection-a')}>Seleccionar colección</button></>}));
vi.mock('../../components/MasterPreview', () => ({MasterPreview: () => null}));
vi.mock('../../components/GenerativeViz', () => ({GenerativeViz: () => null}));
beforeEach(() => {vi.mocked(moveSong).mockResolvedValue({} as never); vi.mocked(listSongs).mockReset().mockResolvedValue({items: [], next: null});});
afterEach(() => {cleanup(); vi.clearAllMocks(); vi.unstubAllGlobals();});
function mount() {return render(<NextIntlClientProvider locale="es" messages={messages}><SongsPage /></NextIntlClientProvider>);}
async function ready() {mount(); await waitFor(() => expect(listSongs).toHaveBeenCalledTimes(1));}
function search(value: string) {fireEvent.change(screen.getByLabelText(messages.songs.searchLabel), {target: {value}});}
test('Enter aplica la búsqueda', async () => {
  await ready(); search('amor');
  fireEvent.keyDown(screen.getByLabelText(messages.songs.searchLabel), {key: 'Enter', code: 'Enter'});
  await waitFor(() => expect(listSongs).toHaveBeenLastCalledWith(expect.objectContaining({q: 'amor'})));
});
test('recargar dependencias conserva la búsqueda aplicada y no usa el borrador', async () => {
  await ready(); search('amor'); fireEvent.click(screen.getByRole('button', {name: messages.songs.search}));
  await waitFor(() => expect(listSongs).toHaveBeenLastCalledWith(expect.objectContaining({q: 'amor'})));
  search('sin aplicar'); fireEvent.click(screen.getByRole('button', {name: 'Seleccionar colección'}));
  await waitFor(() => expect(listSongs).toHaveBeenLastCalledWith(expect.objectContaining({q: 'amor', collection_id: 'collection-a'})));
});
test('una respuesta anterior no sustituye los resultados de la última búsqueda', async () => {
  await ready();
  let resolveOld!: (value: Awaited<ReturnType<typeof listSongs>>) => void;
  vi.mocked(listSongs).mockReturnValueOnce(new Promise(resolve => {resolveOld = resolve;}));
  search('vieja'); fireEvent.click(screen.getByRole('button', {name: messages.songs.search}));
  vi.mocked(listSongs).mockResolvedValueOnce({items: [{id: 'new', title: 'Nueva', status: 'draft'}] as never, next: null});
  search('nueva'); fireEvent.click(screen.getByRole('button', {name: messages.songs.search}));
  await screen.findByRole('heading', {name: 'Nueva'});
  await act(async () => resolveOld({items: [{id: 'old', title: 'Antigua', status: 'draft'}] as never, next: null}));
  expect(screen.queryByRole('heading', {name: 'Antigua'})).toBeNull();
});

const song = (id = 'a', status = 'draft') => ({id, title: `Cancion ${id}`, status, artist: id === 'a' ? 'Artista' : null, style_prompt: 'pop', collection_id: null}) as never;
async function populated() {
  vi.mocked(listSongs).mockResolvedValue({items: [song(), song('b', 'in_progress')], next: null});
  mount(); await screen.findByRole('heading', {name: 'Cancion a'});
  fireEvent.click(screen.getByText('Cargar colecciones'));
}
test('carga mas conserva consulta aplicada y añade resultados', async () => {
  vi.mocked(listSongs).mockResolvedValueOnce({items: [song()], next: 'cursor'});
  mount(); await screen.findByRole('heading', {name: 'Cancion a'});
  vi.mocked(listSongs).mockResolvedValueOnce({items: [song('b')], next: null});
  fireEvent.click(screen.getByRole('button', {name: messages.songs.loadMore}));
  await screen.findByRole('heading', {name: 'Cancion b'});
  expect(screen.getByRole('heading', {name: 'Cancion a'})).toBeTruthy();
  expect(listSongs).toHaveBeenLastCalledWith(expect.objectContaining({cursor: 'cursor'}));
});
test('filtros envian parametros y las vistas y preescucha se alternan', async () => {
  await populated();
  for (const [label, value] of [[messages.songs.filterStatus, 'draft'], [messages.songs.filterModel, 'model'], [messages.songs.filterTag, 'pop'], [messages.songs.filterAfter, '2026-01-01'], [messages.songs.filterBefore, '2026-02-01']]) {
    fireEvent.change(screen.getByLabelText(label), {target: {value}});
  }
  fireEvent.click(screen.getByLabelText(messages.songs.favoriteOnly));
  fireEvent.click(screen.getByRole('button', {name: messages.songs.applyFilters}));
  await waitFor(() => expect(listSongs).toHaveBeenLastCalledWith(expect.objectContaining({status: 'draft', model_id: 'model', tag: 'pop', favorite: true, updated_after: '2026-01-01T00:00:00Z', updated_before: '2026-02-01T23:59:59Z'})));
  fireEvent.click(screen.getByRole('button', {name: messages.songs.list}));
  expect(screen.getByRole('button', {name: messages.songs.list}).getAttribute('aria-pressed')).toBe('true');
  fireEvent.click(screen.getByRole('button', {name: messages.songs.grid}));
  fireEvent.click(screen.getByRole('button', {name: messages.songs.disablePreview}));
  fireEvent.click(screen.getByRole('button', {name: messages.songs.enablePreview}));
});
test('mueve una cancion y una seleccion de canciones sin perder las demas', async () => {
  await populated();
  fireEvent.change(screen.getAllByLabelText(messages.songs.collection)[0], {target: {value: 'collection-a'}});
  await waitFor(() => expect(moveSong).toHaveBeenCalledWith('a', 'collection-a'));
  fireEvent.change(screen.getAllByLabelText(messages.songs.collection)[0], {target: {value: ''}});
  await waitFor(() => expect(moveSong).toHaveBeenCalledWith('a', null));
  const selected = screen.getByLabelText(`${messages.songs.selectSong} Cancion a`);
  fireEvent.click(selected); fireEvent.click(selected); fireEvent.click(selected);
  fireEvent.change(screen.getByLabelText(messages.songs.bulkDestination), {target: {value: 'collection-a'}});
  fireEvent.click(screen.getByRole('button', {name: /Mover.*1/}));
  await waitFor(() => expect((selected as HTMLInputElement).checked).toBe(false));
});
test('errores de mover y eliminar son visibles y eliminar retira solo su cancion', async () => {
  await populated();
  vi.mocked(moveSong).mockRejectedValueOnce(new Error('offline'));
  fireEvent.click(screen.getByLabelText(`${messages.songs.selectSong} Cancion a`));
  fireEvent.change(screen.getByLabelText(messages.songs.bulkDestination), {target: {value: 'collection-a'}});
  fireEvent.click(screen.getByRole('button', {name: /Mover.*1/}));
  expect(await screen.findByRole('alert')).toHaveProperty('textContent', messages.songs.actionError);
  vi.mocked(deleteSong).mockRejectedValueOnce(new Error('offline'));
  fireEvent.click(screen.getAllByRole('button', {name: messages.songs.trash})[0]);
  await waitFor(() => expect(deleteSong).toHaveBeenCalledTimes(1));
  fireEvent.click(screen.getAllByRole('button', {name: messages.songs.trash})[0]);
  await waitFor(() => expect(screen.queryByRole('heading', {name: 'Cancion a'})).toBeNull());
  expect(screen.getByRole('heading', {name: 'Cancion b'})).toBeTruthy();
});
test('papelera permite restaurar y purgar, con errores visibles', async () => {
  await ready();
  vi.mocked(listSongTrash).mockResolvedValue({items: [song(), song('b')], next: null});
  fireEvent.click(screen.getByRole('button', {name: messages.songs.openTrash}));
  await screen.findByRole('heading', {name: 'Cancion a'});
  vi.mocked(restoreSong).mockRejectedValueOnce(new Error('offline'));
  fireEvent.click(screen.getAllByRole('button', {name: messages.songs.restore})[0]);
  expect(await screen.findByRole('alert')).toHaveProperty('textContent', messages.songs.actionError);
  fireEvent.click(screen.getAllByRole('button', {name: messages.songs.restore})[0]);
  await waitFor(() => expect(screen.queryByRole('heading', {name: 'Cancion a'})).toBeNull());
  vi.mocked(purgeSong).mockRejectedValueOnce(new Error('blocked'));
  fireEvent.click(screen.getByRole('button', {name: messages.songs.purge}));
  await waitFor(() => expect(screen.getByRole('alert').textContent).toBe(messages.songs.purgeBlocked));
  fireEvent.click(screen.getByRole('button', {name: messages.songs.purge}));
  expect(await screen.findByText(messages.songs.trashEmpty)).toBeTruthy();
  fireEvent.click(screen.getByRole('button', {name: messages.songs.backToLibrary}));
  expect(await screen.findByText(messages.songs.empty)).toBeTruthy();
});
test('una carga fallida permite reintentar la busqueda aplicada', async () => {
  await ready(); search('amor'); vi.mocked(listSongs).mockRejectedValueOnce(new Error('offline'));
  fireEvent.click(screen.getByRole('button', {name: messages.songs.search}));
  fireEvent.click(await screen.findByRole('button', {name: messages.songs.retryAction}));
  await waitFor(() => expect(listSongs).toHaveBeenLastCalledWith(expect.objectContaining({q: 'amor'})));
  expect(await screen.findByText(messages.songs.empty)).toBeTruthy();
});
