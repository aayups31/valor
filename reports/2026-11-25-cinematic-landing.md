# VALOR landing redesign · November 25, 2026

Reviewed the public OutClass homepage and the local GitLearn site and design notes. The VALOR page adopts the idea of one signature image and a large product reveal. Its artwork, copy, visual identity, and section layout are original to VALOR.

The new landing opens with an obsidian and champagne-gold sculpture, then reveals the actual Command Center, a captioned twenty-second simulation film, and direct links to the evidence and research. Navigation and calls to action use plain text. The film shows the current Command Center and the first observed recovery step in the seeded After damage example. The outcome describes that simulation.

GSAP moves the artwork and brings the workspace into perspective as the visitor scrolls. Motion reverses when scrolling back. Phones use simpler transitions. Reduced motion and plain HTML preserve the content, links, transcript, and native video controls.

The final build passed 13 demo tests. Isolated Chromium confirmed the first keyboard stop, reversible motion, reduced motion, layouts at 320, 390, 768, 821, and 1440 pixels, native video play and seek, the transcript, JavaScript-disabled rendering, and the workspace and Studio links. The video is 19.9 seconds and 2.43 MB. The optimized hero is about 36 KB.

The work is available through the existing local preview. The initial implementation is in `c1f7596` and the closing commit contains final contrast, film, and accessibility refinements. The repository remains the delivery source.

## Hero artwork

Generated with the built-in image tool and optimized to `src/aace/demo/static/landing-hero.webp`. Final generation prompt:

> Create an original ultra-wide 3:2 cinematic editorial hero photograph for VALOR, a premium agent oversight research product. Image is full bleed, extremely dark graphite-black (#08090a), exceptionally elegant and minimal. One hero object only, positioned right-center (center x=72%, y=49%), occupying the right half: a precisely machined monumental split-chevron sculpture resembling two long tapered blades of smoked obsidian and dark brushed titanium, suspended weightlessly, angled slightly in three-quarter perspective, with a single warm pale champagne-gold light on the beveled inside edges. A fine ray of warm light approaches from the left low across the frame and splits into two faint measured curved trajectories behind the object, like an optical experiment. True photorealistic premium product photography, controlled edge lighting, fine realistic material, dark tonality but clear silhouette. The left 47% of the composition must be nearly solid neutral black with no bright objects or texture so white typography can sit over it. Obsidian subtly fades to solid black at every edge. The focal object must be legible even with left side cropped away on narrow displays. Avoid planets, rings around planets, glass cards/tiles, a landscape, UI, fake scientific labels, stars, text, logos, letters, numbers, watermark, rainbow effects, obvious cyberpunk. Think gallery installation photographed on a dark soundstage, sleek dramatic lens figure, black and warm champagne only.
