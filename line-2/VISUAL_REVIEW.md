# Pepe 01 visual and output review

- Wall: `artifacts/line-2/wall.png`, PNG, RGB, **1254 × 1254 px**. This exactly matches the input cave's dimensions and square framing.
- Preview: `dist/line-2/01.jpg`, JPEG, RGB, **512 × 512 px**, 76,192 bytes.
- Record: `dist/line-2/01.json`; number 1, Cave Ice, Wall Line 2. Its image URL uses the SHA-256 of the finished PNG bytes.
- PNG SHA-256: `91b60180e3c0eae1151aee315645029dda7504a806897e355b083e1df631cae8`.

## Chosen review step

Visually inspected the cave input and both generated renders. The first render's upper hand appeared to have four digits, so a targeted second edit added its missing thumb. Counted the final upper hand as four upward/rightward fingers plus one downward thumb, and the lower hand as four fingers plus one thumb: five each. There are no hand stencils. The finished figure has Pepe's wide mouth and large heavy-lidded eyes. Four white pebble circles in each row pair up; the bottom row has one additional red pebble.

The final image retains the input's ceiling, floor, major cracks, warm illumination and square framing. The new marks use charcoal, red/yellow ochre and chalk-like white, with stone texture visible through them. No letters, numbers, captions, signatures, logos, watermark, border, political or hateful symbols, or real people were observed. This was the first Pepe on this wall, so no ancestral marks were present to preserve.

Unmet visual requirements: **none observed on review**. Limitation: a generative edit preserves the cave visually, but does not guarantee pixel-identical geology or lighting outside the painted area. Review is a human-style visual assessment, not an automated guarantee of artistic quality. PNG/JPEG headers, dimensions, record shape, digest, and file size were checked separately with code.

## Generation provenance and prompt

Used the built-in `image_gen.imagegen` tool in edit mode, with `artifacts/ice/cave.png` as the initial edit target and the first result as the correction target. The image tool's generated PNG was copied into the declared wall path. A temporary Pillow checker in disposable `test/scratch/` converted the final wall to the required JPEG preview; it is not a dependency of any delivered code.

Initial prompt: preserve the exact square cave framing, warm rock, cracks, torchlight, ceiling, floor and shadows; add only a worn prehistoric pigment drawing of recognizable Pepe squatting beside two rows of four paired white pebbles with one extra red pebble in the bottom row. Give him a wide mouth, heavy-lidded eyes, and two open five-digit hands; use charcoal, red/yellow ochre and chalk white only, with no writing, logos, frames, or modern rendering.

Final correction prompt: keep the entire cave, Pepe, pebbles and lower hand unchanged; correct only the upper hand by adding one short downward thumb to the four existing upward/rightward fingers. Exactly five separated digits, primitive worn red-ochre/charcoal pigment; no other changes or text.
