export function departmentOptions(departments: string[]): string[] {
  return Array.from(new Set(departments)).sort();
}
