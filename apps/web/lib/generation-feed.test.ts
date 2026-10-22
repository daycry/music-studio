import {expect, test} from 'vitest';
import {createFeedJobs, normalizePeaks} from './generation-feed';

test('expande todos los take_ids de una respuesta en variantes del mismo grupo', () => {
  const jobs = createFeedJobs({
    song_id: 'song-1', generation_job_id: 'job-1', post_job_id: 'post-1',
    take_ids: ['take-a', 'take-b', 'take-c'], beat_job_ids: [],
  });

  expect(jobs).toHaveLength(3);
  expect(jobs.map(job => [job.take_id, job.variant_index, job.group_id])).toEqual([
    ['take-a', 0, 'job-1'], ['take-b', 1, 'job-1'], ['take-c', 2, 'job-1'],
  ]);
  expect(new Set(jobs.map(job => job.job_id))).toEqual(new Set(['job-1']));
});

test('mantiene una tarjeta para respuestas antiguas sin take_ids', () => {
  const jobs = createFeedJobs({song_id: 'song-1', generation_job_id: 'job-1', post_job_id: 'post-1', take_ids: [], beat_job_ids: []});
  expect(jobs).toHaveLength(1);
  expect(jobs[0].take_id).toBeUndefined();
});

test('normaliza los peaks publicados por el endpoint de takes', () => {
  expect(normalizePeaks({data: [[[.1, .8, .3]]]})).toEqual([.1, .8, .3]);
  expect(normalizePeaks({data: [[.1, 1.2, -.2, Number.NaN]]})).toEqual([.1, 1, 0]);
  expect(normalizePeaks({data: []})).toBeNull();
});
