/* WanderMind — script.js — shared utilities */

// ── Active nav link ──────────────────────────────────────────
(function () {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });
})();

// ── Intersection observer for cards ─────────────────────────
(function () {
  if (!('IntersectionObserver' in window)) return;
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e, i) => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.feat-card, .day-card, .trip-card, .exp-card').forEach(c => {
    obs.observe(c);
  });
})();