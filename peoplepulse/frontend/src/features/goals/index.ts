export function progressExplanation(percentage: number): string {
  return `Weighted progress is ${percentage.toFixed(1)}% from valid key-result actual/target values and weights.`;
}
