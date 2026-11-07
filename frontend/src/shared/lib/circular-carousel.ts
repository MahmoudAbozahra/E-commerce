export function circularOffset(index: number, activeIndex: number, itemCount: number) {
  if (itemCount <= 1) return 0;

  const forward = ((index - activeIndex) % itemCount + itemCount) % itemCount;
  const backward = forward - itemCount;
  return Math.abs(forward) <= Math.abs(backward) ? forward : backward;
}

export function circularIndex(index: number, itemCount: number) {
  if (itemCount <= 0) return 0;
  return ((index % itemCount) + itemCount) % itemCount;
}
