/** Format a calendar day using the browser's local timezone, not UTC. */
export function localDateInputValue(date = new Date()): string {
  const offsetMilliseconds = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMilliseconds).toISOString().slice(0, 10);
}
