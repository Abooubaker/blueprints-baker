"use client";

import { useEffect, useRef } from "react";

import { assetPath } from "@/lib/constants";

const TRAIL = [
  { dx: -46, dy: -10, size: 14, tone: "voxel-gold" },
  { dx: -86, dy: 6, size: 11, tone: "voxel-champagne" },
  { dx: -122, dy: -4, size: 8, tone: "voxel-burgundy" },
];

/**
 * A fixed bird that glides down the page as you scroll, leaving a trail of blocks,
 * plus a Minecraft-style XP bar that fills with scroll progress.
 */
export function ScrollCompanion() {
  const birdRef = useRef<HTMLDivElement>(null);
  const trailRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const fillRef = useRef<HTMLDivElement>(null);
  const levelRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let lastY = window.scrollY;
    let velocity = 0;
    let frame = 0;
    let idle = 0;

    function update() {
      frame = 0;
      const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
      const progress = Math.min(1, Math.max(0, window.scrollY / max));
      const vh = window.innerHeight;
      const y = vh * (0.14 + progress * 0.58);
      const sway = reduce ? 0 : Math.sin(progress * Math.PI * 6) * 34;
      const tilt = reduce ? 0 : Math.max(-16, Math.min(16, velocity * 0.4));

      if (birdRef.current) {
        birdRef.current.style.transform = `translate3d(${sway}px, ${y}px, 0) rotate(${tilt}deg)`;
      }
      TRAIL.forEach((block, index) => {
        const el = trailRefs.current[index];
        if (el) {
          el.style.transform = `translate3d(${sway + block.dx * 1.4}px, ${y + 44 + block.dy}px, 0)`;
        }
      });
      if (fillRef.current) fillRef.current.style.width = `${(progress * 100).toFixed(1)}%`;
      if (levelRef.current) levelRef.current.textContent = String(Math.round(progress * 30));
    }

    function onScroll() {
      velocity = window.scrollY - lastY;
      lastY = window.scrollY;
      if (!frame) frame = window.requestAnimationFrame(update);
      window.clearTimeout(idle);
      idle = window.setTimeout(() => {
        velocity = 0;
        update();
      }, 140);
    }

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", update);
      window.clearTimeout(idle);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div aria-hidden="true">
      {TRAIL.map((block, index) => (
        <span
          key={block.tone}
          ref={(el) => {
            trailRefs.current[index] = el;
          }}
          className={`companion-trail voxel ${block.tone}`}
          style={{
            width: block.size,
            height: block.size,
            transitionDuration: `${0.25 + index * 0.18}s`,
          }}
        />
      ))}
      <div ref={birdRef} className="companion-bird">
        <div
          className="companion-bird-art"
          style={{ backgroundImage: `url(${assetPath("/brand/albayraq-bird.png")})` }}
        />
      </div>
      <div className="xp-wrap">
        <span ref={levelRef} className="xp-level">
          0
        </span>
        <div className="xp-bar">
          <div ref={fillRef} className="xp-fill" />
        </div>
      </div>
    </div>
  );
}
