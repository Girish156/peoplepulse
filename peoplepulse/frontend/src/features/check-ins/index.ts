export function snapshotKeys(snapshot: Record<string, number> | null | undefined): string {
  if (!snapshot) return "";
  return Object.keys(snapshot).join(", ");
}
