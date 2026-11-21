# Demo design decisions

Approved direction: **DIA Studio / Toolkit B**. This extends the approved main-screen study, not the source website's brand, photography or artwork.

Primary task: Search, filter or sort the sixteen English collection files. Next action: Inspect an original, select files, and compare their SHA-256 with the included manifest.

Use the approved composition, system typefaces, flat rules and real example evidence. Keep one task per region, explicit disabled/error/success states and visible keyboard focus. No decorative status badges, third-party branding or fake model output.

The UI and new example content are English only, as requested. Original media stays byte-identical; layout uses normal CSS fitting, with no image preprocessing or postprocessing. Narrow layouts prioritize work and controls; Longform uses a real chapter column so navigation cannot cover the editor.

Verified layouts: 1280×720 browser viewport, 390×660 and 820×660 same-origin responsive iframes. These are layout checks, not physical-device certification. The browser default inner content width varies with scrollbar space.
