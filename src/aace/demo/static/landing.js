"use strict";

(() => {
  const video = document.getElementById("demo-video");
  const player = document.getElementById("play-demo");
  const videoError = document.getElementById("film-error");
  if (video && player && videoError) {
    const showVideoError = () => {
      player.hidden = true;
      videoError.hidden = false;
    };
    player.hidden = false;
    if (video.error) showVideoError();
    player.addEventListener("click", async () => {
      try {
        await video.play();
        video.focus({ preventScroll: true });
      } catch {
        showVideoError();
        video.focus({ preventScroll: true });
      }
    });
    video.addEventListener("error", showVideoError);
    video.addEventListener("play", () => { player.hidden = true; videoError.hidden = true; });
    video.addEventListener("ended", () => { player.hidden = false; });
  }

  const { gsap, ScrollTrigger } = window;
  if (!gsap || !ScrollTrigger) return;

  gsap.registerPlugin(ScrollTrigger);
  gsap.matchMedia().add({
    all: "all",
    desktop: "(min-width: 900px)",
    reduce: "(prefers-reduced-motion: reduce)",
  }, ({ conditions }) => {
    if (conditions.reduce) return;

    const enter = gsap.utils.toArray(".hero-copy [data-enter]");
    if (enter.length) {
      gsap.from(enter, {
        y: 16,
        opacity: 0.86,
        duration: 0.8,
        stagger: 0.09,
        ease: "power3.out",
        clearProps: "transform,opacity",
      });
    }

    const orbit = document.querySelector(".hero-orbit");
    const showcase = document.querySelector(".hero-showcase");
    const frame = showcase?.querySelector(".product-frame");
    if (frame) {
      gsap.fromTo(frame, {
        y: conditions.desktop ? 22 : 12,
        rotationX: conditions.desktop ? 5 : 0,
        scale: 0.976,
        transformPerspective: 1400,
        transformOrigin: "50% 40%",
      }, {
        y: 0,
        rotationX: 0,
        scale: 1,
        ease: "none",
        scrollTrigger: { trigger: showcase, start: "top 92%", end: "bottom 70%", scrub: 0.65 },
      });
    }
    if (orbit && showcase && conditions.desktop) {
      gsap.to(orbit, {
        yPercent: 11,
        xPercent: 4,
        ease: "none",
        scrollTrigger: { trigger: showcase, start: "top bottom", end: "bottom top", scrub: 0.8 },
      });
    }

    const film = document.querySelector(".film-section");
    const filmShell = film?.querySelector(".film-shell");
    const filmOrbit = film?.querySelector(".film-orbit");
    if (filmShell) {
      gsap.fromTo(filmShell, { scale: 0.964, y: 16 }, {
        scale: 1,
        y: 0,
        ease: "none",
        scrollTrigger: { trigger: film, start: "top 94%", end: "top 34%", scrub: 0.6 },
      });
    }
    if (filmOrbit && conditions.desktop) {
      gsap.fromTo(filmOrbit, { xPercent: -5, yPercent: 4 }, {
        xPercent: 8,
        yPercent: -4,
        ease: "none",
        scrollTrigger: { trigger: film, start: "top bottom", end: "bottom top", scrub: 0.85 },
      });
    }

    for (const reveal of gsap.utils.toArray("[data-reveal]")) {
      gsap.from(reveal, {
        y: 18,
        opacity: 0.84,
        duration: 0.65,
        ease: "power2.out",
        scrollTrigger: {
          trigger: reveal,
          start: "top 88%",
          toggleActions: "play none none reverse",
        },
      });
    }
  });
})();
