"use strict";

(() => {
  const story = document.querySelector("#story");
  const film = document.querySelector("#film");
  const fallback = document.querySelector("#standby");
  const stage = document.querySelector(".stage");
  const counter = document.querySelector("#counter");
  const view = document.querySelector("#view-name");
  const moments = [...document.querySelectorAll(".moment")];
  const motion = window.matchMedia("(prefers-reduced-motion: no-preference) and (min-height: 530px)");
  let cleanup;

  function mount() {
    cleanup?.();
    if (!motion.matches) return;

    const controller = new AbortController();
    const options = { signal: controller.signal };
    document.body.classList.add("scrub");
    let active = -1;
    let fraction = 0;
    let frame = 0;
    let visible = false;
    let mediaFailed = false;

    function syncFilm() {
      if (!Number.isFinite(film.duration) || film.seeking || mediaFailed) return;
      const target = Math.min(film.duration - 1 / 24, fraction * film.duration);
      if (Math.abs(film.currentTime - target) > 1 / 24) {
        film.currentTime = target;
      } else if (film.readyState >= 2) {
        film.classList.add("ready");
      }
    }

    function draw() {
      frame = 0;
      if (!visible) return;
      const phone = window.innerWidth <= 750;
      const focus = phone
        ? stage.getBoundingClientRect().height + (window.innerHeight - stage.offsetHeight) * .42
        : window.innerHeight * .5;
      const bounds = moments.map(moment => moment.getBoundingClientRect());
      const index = Math.max(0, bounds.findLastIndex(rect => rect.top <= focus));
      const within = Math.max(0, Math.min(.999, (focus - bounds[index].top) / bounds[index].height));
      fraction = (index + within) / moments.length;
      if (index !== active) {
        active = index;
        film.classList.remove("ready");
        view.textContent = moments[index].dataset.view;
        counter.textContent = String(index + 1).padStart(2, "0") + " / 04";
        fallback.style.setProperty("--plate", (index / (moments.length - 1)) * 100 + "%");
      }
      stage.style.setProperty("--progress", fraction);
      syncFilm();
    }

    function schedule() {
      if (!frame && visible) frame = requestAnimationFrame(draw);
    }

    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible && !film.hasAttribute("src") && film.canPlayType("video/webm")) {
        film.src = film.dataset.src;
        film.preload = "auto";
        film.load();
      }
      schedule();
    }, { rootMargin: "15% 0px" });
    observer.observe(story);
    window.addEventListener("scroll", schedule, { ...options, passive: true });
    window.addEventListener("resize", schedule, options);
    film.addEventListener("loadeddata", schedule, options);
    film.addEventListener("seeked", schedule, options);
    film.addEventListener("error", () => {
      mediaFailed = true;
      film.classList.remove("ready");
    }, options);

    let choreography;
    if (window.gsap && window.ScrollTrigger) {
      gsap.registerPlugin(ScrollTrigger);
      choreography = gsap.context(() => {
        gsap.fromTo(".surface", { rotationX: 6, scale: .965 }, {
          rotationX: 0, scale: 1, ease: "none",
          scrollTrigger: { trigger: ".hero-product", start: "top 85%", end: "center 45%", scrub: true }
        });
        gsap.fromTo(".directory a", { y: 18 }, {
          y: 0, stagger: .12, ease: "none",
          scrollTrigger: { trigger: ".directory", start: "top 95%", end: "center 70%", scrub: true }
        });
      });
    }

    cleanup = () => {
      controller.abort();
      observer.disconnect();
      cancelAnimationFrame(frame);
      choreography?.revert();
      film.removeAttribute("src");
      film.load();
      film.classList.remove("ready");
      document.body.classList.remove("scrub");
      cleanup = undefined;
    };
  }

  mount();
  motion.addEventListener("change", mount);
})();
