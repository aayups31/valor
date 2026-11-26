"use strict";

(() => {
  const film = document.getElementById("film");
  const chapters = document.getElementById("chapters");
  const buttons = Array.from(chapters.querySelectorAll("button"));
  const times = buttons.map(button => Number(button.dataset.time));
  const notice = document.getElementById("film-status");
  let requestedTime = null;

  function markChapter() {
    const active = times.findLastIndex(time => time <= film.currentTime);
    buttons.forEach((button, index) => {
      if (index === active) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
  }

  function seekRequestedTime() {
    if (requestedTime === null || film.readyState < HTMLMediaElement.HAVE_METADATA) return;
    film.currentTime = requestedTime;
    requestedTime = null;
    markChapter();
  }

  function playbackError() {
    notice.hidden = false;
    chapters.hidden = true;
  }

  buttons.forEach((button, index) => {
    button.addEventListener("click", () => {
      requestedTime = times[index];
      seekRequestedTime();
      film.play().catch(error => {
        if (error.name !== "AbortError") notice.hidden = false;
      });
    });
  });
  film.addEventListener("loadedmetadata", seekRequestedTime);
  film.addEventListener("timeupdate", markChapter);
  film.addEventListener("seeked", markChapter);
  film.addEventListener("error", playbackError);
  film.querySelector("source").addEventListener("error", playbackError);
  if (film.error) playbackError();
  else chapters.hidden = false;
  markChapter();

  const { gsap, ScrollTrigger } = window;
  if (!gsap || !ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);
  gsap.matchMedia().add("(min-width: 821px) and (prefers-reduced-motion: no-preference)", () => {
    gsap.from(".cover-copy > *", {
      y: 12, duration: .7, stagger: .07, ease: "power2.out", clearProps: "transform",
    });
    gsap.fromTo(".cover-art img", { scale: 1.015 }, {
      scale: 1.09, yPercent: 5, ease: "none",
      scrollTrigger: { trigger: ".cover", start: "top top", end: "bottom top", scrub: .5 },
    });
    gsap.from(".workspace-image", {
      y: 28, ease: "none",
      scrollTrigger: { trigger: ".workspace-layout", start: "top 95%", end: "top 45%", scrub: .5 },
    });
  });
})();
