export function formatLocalTime(isoTs: string | null | undefined): string {
  if (!isoTs) return "—";

  return new Date(isoTs).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
