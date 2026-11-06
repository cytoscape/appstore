// Builds the zip archives the submission specs upload: Cytoscape Web bundles and desktop app jars.
// Entries are stored uncompressed, which every zip reader accepts.

const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
  return c >>> 0
})

function crc32(data: Buffer): number {
  let crc = 0xffffffff
  for (const byte of data) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8)
  return (crc ^ 0xffffffff) >>> 0
}

export function zip(entries: Record<string, string>): Buffer {
  const locals: Buffer[] = []
  const centrals: Buffer[] = []
  let offset = 0
  for (const [path, content] of Object.entries(entries)) {
    const name = Buffer.from(path)
    const data = Buffer.from(content)
    const crc = crc32(data)

    const local = Buffer.alloc(30)
    local.writeUInt32LE(0x04034b50, 0)
    local.writeUInt16LE(20, 4)
    local.writeUInt32LE(crc, 14)
    local.writeUInt32LE(data.length, 18)
    local.writeUInt32LE(data.length, 22)
    local.writeUInt16LE(name.length, 26)
    locals.push(local, name, data)

    const central = Buffer.alloc(46)
    central.writeUInt32LE(0x02014b50, 0)
    central.writeUInt16LE(20, 4)
    central.writeUInt16LE(20, 6)
    central.writeUInt32LE(crc, 16)
    central.writeUInt32LE(data.length, 20)
    central.writeUInt32LE(data.length, 24)
    central.writeUInt16LE(name.length, 28)
    central.writeUInt32LE(offset, 42)
    centrals.push(central, name)

    offset += local.length + name.length + data.length
  }
  const centralSize = centrals.reduce((size, part) => size + part.length, 0)
  const end = Buffer.alloc(22)
  end.writeUInt32LE(0x06054b50, 0)
  end.writeUInt16LE(Object.keys(entries).length, 8)
  end.writeUInt16LE(Object.keys(entries).length, 10)
  end.writeUInt32LE(centralSize, 12)
  end.writeUInt32LE(offset, 16)
  return Buffer.concat([...locals, ...centrals, end])
}

export function webBundle(name: string, version: string, id = 'itbundle') {
  return {
    name: `${id}-${version}.zip`,
    mimeType: 'application/zip',
    buffer: zip({
      'dist/remoteEntry.js': 'var itbundle;',
      'dist/cy-manifest.json': JSON.stringify({ id, name, version }),
    }),
  }
}

export function desktopJar(name: string, version: string) {
  const manifest = [
    'Manifest-Version: 1.0',
    'Bundle-ManifestVersion: 2',
    'Bundle-SymbolicName: org.cytoscape.it.app',
    `Bundle-Name: ${name}`,
    `Bundle-Version: ${version}`,
    'Import-Package: org.cytoscape.model;version="[3.7,4)"',
    '',
    '',
  ].join('\r\n')
  return {
    name: `it-app-${version}.jar`,
    mimeType: 'application/java-archive',
    buffer: zip({ 'META-INF/MANIFEST.MF': manifest }),
  }
}
