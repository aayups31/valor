"use strict";

(() => {
  const video = document.getElementById("demo-video");
  const player = document.getElementById("play-demo");
  const videoError = document.getElementById("film-error");

  function showVideoError() {
    player.hidden = true;
    videoError.hidden = false;
  }

  player.hidden = Boolean(video.error);
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
  video.addEventListener("play", () => {
    player.hidden = true;
    videoError.hidden = true;
  });
  video.addEventListener("ended", () => { player.hidden = false; });

  const { gsap, ScrollTrigger } = window;
  if (!gsap || !ScrollTrigger) return;

  gsap.registerPlugin(ScrollTrigger);
  gsap.matchMedia().add({
    all: "all",
    wide: "(min-width: 821px)",
    reduced: "(prefers-reduced-motion: reduce)"
  }, ({ conditions }) => {
    if (conditions.reduced) return;

    gsap.from("[data-enter]", {
      y: 20, opacity: .78, duration: .85, stagger: .085,
      ease: "power3.out", clearProps: "transform,opacity",
    });

    gsap.to(".page-progress", {
      scaleX: 1, ease: "none",
      scrollTrigger: { start: 0, end: "max", scrub: true },
    });

    if (conditions.wide) {
      const exit = gsap.timeline({
        defaults: { ease: "none" },
        scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: .6 },
      });
      exit.to(".hero-image", { yPercent: 18, scale: 1.1, opacity: .58 }, 0);
      exit.to(".scroll-cue", { opacity: .4, y: 12 }, 0);

      gsap.fromTo(".product-frame", {
        y: 40, rotationX: 5, scale: .96, opacity: .72,
      }, {
        y: 0, rotationX: 0, scale: 1, opacity: 1, ease: "none",
        scrollTrigger: { trigger: ".product-figure", start: "top 94%", end: "top 40%", scrub: .65 },
      });

      gsap.fromTo(".film-media", { scale: .96 }, {
        scale: 1, ease: "none",
        scrollTrigger: { trigger: ".film-shell", start: "top 96%", end: "top 42%", scrub: .65 },
      });
    }

    for (const element of gsap.utils.toArray("[data-reveal]")) {
      gsap.from(element, {
        y: conditions.wide ? 26 : 12,
        opacity: .72,
        duration: .7,
        ease: "power3.out",
        scrollTrigger: {
          trigger: element,
          start: "top 93%",
          toggleActions: "play none none reverse",
        },
      });
    }
  });
})();
