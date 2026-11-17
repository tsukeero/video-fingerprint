#!/usr/bin/env node
// vfp-js FILE...  prints `<fingerprint>  <path>` per file (errors to stderr, exit code 1).
import process from 'node:process';
import { fingerprintPath } from './path.js';

let failed = false;
for (const p of process.argv.slice(2)) {
  try {
    console.log(`${await fingerprintPath(p)}  ${p}`);
  } catch (e) {
    console.error(`${p}: ${e.message}`);
    failed = true;
  }
}
process.exitCode = failed ? 1 : 0;
