#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');

async function main() {
  const [input, outputBase] = process.argv.slice(2);
  if (!input || !outputBase) {
    throw new Error('CEW_OAR_SHARP_USAGE');
  }
  if (!fs.existsSync(input)) {
    throw new Error('CEW_OAR_SHARP_INPUT_MISSING');
  }

  fs.mkdirSync(path.dirname(outputBase), { recursive: true });
  const info = await sharp(input, { sequentialRead: true, limitInputPixels: false })
    .jpeg({ quality: 88 })
    .tile({ layout: 'dz', size: 256, overlap: 1, depth: 'onepixel', container: 'fs' })
    .toFile(`${outputBase}.dz`);

  const packageMeta = require('sharp/package.json');
  process.stdout.write(JSON.stringify({
    state: 'CEW_OAR_SHARP_DEEPZOOM_PASS',
    sharp_version: packageMeta.version,
    sharp_license: packageMeta.license,
    bundled_libvips_version: sharp.versions.vips,
    output_format: info.format || null
  }) + '\n');
}

main().catch((error) => {
  console.error('CEW_OAR_SHARP_DEEPZOOM_FAIL');
  process.exitCode = 1;
});
