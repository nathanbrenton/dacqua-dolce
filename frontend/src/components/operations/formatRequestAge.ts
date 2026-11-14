// Short "how long ago" label: "Just now", "12m", "5h", "3d", then a date.
export function formatRequestAge(createdAt: string, now: number = Date.now()): string {
  const created = new Date(createdAt);
  const minutes = Math.floor((now - created.getTime()) / 60000);
  if (minutes < 1) {
    return "Just now";
  }
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h`;
  }
  const days = Math.floor(hours / 24);
  if (days < 14) {
    return `${days}d`;
  }
  return created.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
