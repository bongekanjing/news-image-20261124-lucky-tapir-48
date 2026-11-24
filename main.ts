/**
 * Entry point for "Sum up 24 November's world news in one image".
 *
 * What this program does is deliberately small: the page is pre-rendered in
 * `entry.png` by `draw.py` beside this file, and at grade time this program
 * places those exact bytes at `$MAKEFUN_OUTPUT_DIR/entry.png`.
 *
 * Why copy instead of draw at run time. The grader executes the program twice
 * and compares the two outputs byte for byte. Copying bytes is deterministic
 * by construction. Re-rendering text is only deterministic if the font files,
 * the rasteriser and its hinting all match between runs, and the sandbox gives
 * no such guarantee, so a redraw risks a nondeterministic failure for no gain
 * in what the judge actually scores.
 *
 * Why the checks. The gate refuses an entry whose image breaks a stated limit,
 * and a refused entry scores zero without the judge ever seeing it. A wrong
 * file handed to the grader fails silently; a wrong file caught here fails
 * loudly with a reason. So before writing anything out this program reads the
 * PNG's own header and confirms the four things the rules constrain: that the
 * signature is PNG, that the IHDR chunk is present and well formed, that each
 * edge is within 1024, and that the file is within 1 MiB. It decodes no pixels.
 *
 * Node 22, standard library only, no network.
 */

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

/** The rules: at most 1024 pixels on either edge, at most 1 MiB of file. */
const EDGE_LIMIT = 1024;
const BYTE_LIMIT = 1048576;

/** The eight bytes every PNG opens with, as required by the format. */
const PNG_MARK = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function refuse(reason: string): never {
  throw new Error(`entry.png rejected before output: ${reason}`);
}

/**
 * Read width and height straight out of the IHDR chunk.
 *
 * A PNG that follows the format puts a 13-byte IHDR payload at a fixed offset:
 * bytes 8..11 are the length, 12..15 the chunk type, then the big-endian width
 * and height. Checking the type string matters, since a file with a valid
 * signature but a different first chunk is not an image the gate will take.
 */
function edgesOf(buf: Buffer): { w: number; h: number } {
  if (buf.length < 33) refuse("file is too short to hold a PNG header");
  if (!buf.subarray(0, 8).equals(PNG_MARK)) refuse("missing the PNG signature");

  const chunkType = buf.subarray(12, 16).toString("latin1");
  if (chunkType !== "IHDR") refuse(`first chunk is ${chunkType}, not IHDR`);
  if (buf.readUInt32BE(8) !== 13) refuse("IHDR is not the expected 13 bytes");

  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

const bytes = readFileSync(source);

if (bytes.length > BYTE_LIMIT) {
  refuse(`${bytes.length} bytes is over the ${BYTE_LIMIT} limit`);
}

const { w, h } = edgesOf(bytes);
if (w > EDGE_LIMIT || h > EDGE_LIMIT) {
  refuse(`${w}x${h} is larger than ${EDGE_LIMIT} on an edge`);
}
if (w < 1 || h < 1) refuse(`${w}x${h} is not a drawable size`);

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, "entry.png"), bytes);

console.log(`wrote entry.png ${w}x${h}, ${bytes.length} bytes`);
