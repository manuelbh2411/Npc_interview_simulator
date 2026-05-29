(() => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const hasFinePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  if (prefersReducedMotion || !hasFinePointer) {
    return;
  }

  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d", { alpha: true });
  if (!context) {
    return;
  }

  canvas.className = "cursor-trail-canvas";
  canvas.setAttribute("aria-hidden", "true");
  document.body.appendChild(canvas);

  const particles = [];
  const colors = ["79, 226, 214", "243, 185, 91", "107, 168, 255"];
  let width = 0;
  let height = 0;
  let raf = 0;
  let lastX = 0;
  let lastY = 0;
  let lastSpawn = 0;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function spawn(x, y) {
    const now = performance.now();
    const distance = Math.hypot(x - lastX, y - lastY);
    if (now - lastSpawn < 14 && distance < 9) {
      return;
    }

    lastX = x;
    lastY = y;
    lastSpawn = now;

    particles.push({
      x,
      y,
      vx: (Math.random() - 0.5) * 0.9,
      vy: (Math.random() - 0.5) * 0.9,
      age: 0,
      life: 420 + Math.random() * 240,
      radius: 5 + Math.random() * 10,
      color: colors[Math.floor(Math.random() * colors.length)],
    });

    if (particles.length > 90) {
      particles.splice(0, particles.length - 90);
    }
  }

  function draw(timestamp) {
    context.clearRect(0, 0, width, height);

    for (let index = particles.length - 1; index >= 0; index -= 1) {
      const particle = particles[index];
      particle.age += 16;
      particle.x += particle.vx;
      particle.y += particle.vy;

      const progress = particle.age / particle.life;
      if (progress >= 1) {
        particles.splice(index, 1);
        continue;
      }

      const alpha = (1 - progress) * 0.36;
      const radius = particle.radius * (1 - progress * 0.72);
      const gradient = context.createRadialGradient(
        particle.x,
        particle.y,
        0,
        particle.x,
        particle.y,
        radius,
      );
      gradient.addColorStop(0, `rgba(${particle.color}, ${alpha})`);
      gradient.addColorStop(1, `rgba(${particle.color}, 0)`);
      context.fillStyle = gradient;
      context.beginPath();
      context.arc(particle.x, particle.y, radius, 0, Math.PI * 2);
      context.fill();
    }

    if (particles.length || timestamp - lastSpawn < 800) {
      raf = window.requestAnimationFrame(draw);
    } else {
      raf = 0;
    }
  }

  window.addEventListener("resize", resize, { passive: true });
  window.addEventListener("pointermove", (event) => {
    spawn(event.clientX, event.clientY);
    if (!raf) {
      raf = window.requestAnimationFrame(draw);
    }
  }, { passive: true });

  resize();
})();
