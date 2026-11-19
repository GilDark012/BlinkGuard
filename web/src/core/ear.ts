export interface Point {
  x: number;
  y: number;
}

const distance = (a: Point, b: Point): number => Math.hypot(a.x - b.x, a.y - b.y);

/**
 * Eye Aspect Ratio: EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
 *
 * @param eye 6 points in order [outer corner, top 1, top 2, inner corner, bottom 1, bottom 2]
 * @returns the EAR, or 0 for degenerate input
 */
export function calculateEar(eye: readonly Point[]): number {
  const [p1, p2, p3, p4, p5, p6] = eye;
  if (!p1 || !p2 || !p3 || !p4 || !p5 || !p6) return 0;
  const horizontal = distance(p1, p4);
  if (horizontal === 0) return 0;
  return (distance(p2, p6) + distance(p3, p5)) / (2 * horizontal);
}
