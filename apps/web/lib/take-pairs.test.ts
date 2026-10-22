import {describe, expect, test} from 'vitest';
import {findPairedTake, type PairableTake} from './take-pairs';

describe('findPairedTake', () => {
  const takes: PairableTake[] = [
    {id: 'a', batch_id: 'batch', variant_index: 0},
    {id: 'b', batch_id: 'batch', variant_index: 1},
    {id: 'c', batch_id: 'other', variant_index: 0},
  ];
  test('encuentra la variante hermana del mismo lote', () => {
    expect(findPairedTake(takes, takes[0])?.id).toBe('b');
    expect(findPairedTake(takes, takes[1])?.id).toBe('a');
  });
  test('no cruza lotes cuando falta la pareja', () => {
    expect(findPairedTake(takes, takes[2])).toBeNull();
  });
});
