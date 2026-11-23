// Card previews come from verified file bytes, never hand-written poster slogans.
export function textPreview(bytes) {
  return new TextDecoder("utf-8", { fatal: true })
    .decode(bytes)
    .split(/\r?\n/)
    .filter((line) => line.trim())
    .slice(0, 7)
    .map((line) => line.slice(0, 100));
}
