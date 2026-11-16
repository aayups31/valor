# Integrated landing page — November 15, 2026

Rebuilt the landing composition around the supplied black-and-gold references. Added a larger typographic hero, refreshed the product preview from the redesigned Command Center, removed its enclosing browser-style frame, and integrated a three-chapter walkthrough directly into the page. A sticky Agent → VALOR → Work illustration reveals the selected recovery plan and observed health as the reader scrolls. The demo video now sits in an open cinematic section with native controls, captions and transcript retained.

Motion: local GSAP 3.15.1 and ScrollTrigger; reversible product perspective, orbital parallax, chapter entrances, signal movement, selected-plan reveal, observed-result reveal, film framing and section transitions. Desktop gets the sticky walkthrough; mobile gets a normal readable flow. Reduced-motion preference removes the animation triggers. Content and links remain available without GSAP.

Verification: isolated Chrome passed 15-trigger initialization, reverse scrolling, reduced-motion teardown, video playback and seeking, 1440px and 390px layouts, product and instrument links, and no runtime errors. Reviewed desktop, story and phone screenshots. Corrected decorative orbit overflow found during the first phone check. JavaScript syntax and Git whitespace checks passed.

Scope: the illustrated walkthrough describes the existing seeded After damage example; it is not a live agent connection. The video remains the earlier illustrated simulation recording and includes the earlier Command Center appearance. No research or production claims were added. The current workspace opens at /app. No external services or paid dependencies.

Version control: main redesign committed as 4d62813; final mobile correction and report in the subsequent commit. Both pushed to origin/main at completion. Next: review the landing page in the local browser; refresh the film if a recording of the latest product screens is desired.

Final automated check: 13 demo tests passed in 8.25 seconds, including asset delivery and video seeking support.
