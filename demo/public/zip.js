// Standard ZIP, uncompressed entries. Byte-preserving packaging, no image operations.
const table = Uint32Array.from({ length: 256 }, (_, n) => {
  for (let k = 0; k < 8; k++) n = n & 1 ? 0xedb88320 ^ (n >>> 1) : n >>> 1;
  return n >>> 0;
});
export function crc32(bytes) {
  let n = 0xffffffff;
  for (const b of bytes) n = table[(n ^ b) & 255] ^ (n >>> 8);
  return (n ^ 0xffffffff) >>> 0;
}
export function zipStore(files) {
  const parts = [],
    central = [];
  let offset = 0,
    total = 0;
  const view = (n) => new DataView(new ArrayBuffer(n));
  for (const file of files) {
    if (
      !/^[a-zA-Z0-9_./-]+$/.test(file.name) ||
      file.name.includes("..") ||
      file.name.startsWith("/")
    )
      throw new Error("Unsafe package filename.");
    const name = new TextEncoder().encode(file.name),
      bytes = file.bytes,
      crc = crc32(bytes),
      header = view(30 + name.length);
    header.setUint32(0, 0x04034b50, true);
    header.setUint16(4, 20, true);
    header.setUint16(6, 0x800, true);
    header.setUint16(12, 0x21, true);
    header.setUint32(14, crc, true);
    header.setUint32(18, bytes.length, true);
    header.setUint32(22, bytes.length, true);
    header.setUint16(26, name.length, true);
    new Uint8Array(header.buffer).set(name, 30);
    parts.push(new Uint8Array(header.buffer), bytes);
    const record = view(46 + name.length);
    record.setUint32(0, 0x02014b50, true);
    record.setUint16(4, 20, true);
    record.setUint16(6, 20, true);
    record.setUint16(8, 0x800, true);
    record.setUint16(14, 0x21, true);
    record.setUint32(16, crc, true);
    record.setUint32(20, bytes.length, true);
    record.setUint32(24, bytes.length, true);
    record.setUint16(28, name.length, true);
    record.setUint32(42, offset, true);
    new Uint8Array(record.buffer).set(name, 46);
    central.push(new Uint8Array(record.buffer));
    total += record.byteLength;
    offset += header.byteLength + bytes.length;
  }
  if (files.length > 65535) throw new Error("Too many files.");
  const end = view(22);
  end.setUint32(0, 0x06054b50, true);
  end.setUint16(8, files.length, true);
  end.setUint16(10, files.length, true);
  end.setUint32(12, total, true);
  end.setUint32(16, offset, true);
  return new Blob([...parts, ...central, end.buffer], {
    type: "application/zip",
  });
}
