export type PairableTake = {id:string; batch_id?:string|null; root_id?:string|null; variant_index?:number};

export function findPairedTake<T extends PairableTake>(takes: T[], current: T): T | null {
  const groupKey = current.batch_id ?? current.root_id;
  if (!groupKey || current.variant_index === undefined) return null;
  const siblings = takes.filter(item => item.id !== current.id && (item.batch_id ?? item.root_id) === groupKey);
  if (!siblings.length) return null;
  const opposite = siblings.find(item => item.variant_index !== undefined && item.variant_index !== current.variant_index);
  return opposite ?? siblings[0] ?? null;
}
