export function previewOverall(goalScore: number, feedbackScore: number): number {
  return Number((goalScore * 0.5 + feedbackScore * 0.5).toFixed(2));
}
