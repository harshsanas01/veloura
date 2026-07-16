import { useEffect, useState } from "react";
import type { ImgHTMLAttributes } from "react";

import { cn } from "@/utils/cn";

// Inline SVG so the fallback can never itself fail to load. Neutral hanger
// mark on the same taupe wash the image containers already use.
const FALLBACK_IMAGE =
  "data:image/svg+xml," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 1200">` +
      `<rect width="900" height="1200" fill="#efeae3"/>` +
      `<g stroke="#b8ac9c" stroke-width="22" fill="none" stroke-linecap="round" stroke-linejoin="round">` +
      `<path d="M450 480c0-40 32-64 64-64s64 26 64 66-38 54-64 78"/>` +
      `<path d="M514 560v40L260 720h508L514 600"/>` +
      `</g>` +
      `<text x="450" y="820" font-family="Georgia, serif" font-size="42" fill="#b8ac9c" text-anchor="middle">Image unavailable</text>` +
    `</svg>`
  );

type Props = ImgHTMLAttributes<HTMLImageElement> & { src?: string };

/**
 * Drop-in <img> replacement for product imagery: lazy loading, an animated
 * skeleton while the real image streams in, and a self-contained fallback
 * that only appears if the real image fails (or no URL was provided). Must be
 * rendered inside a `relative` container (all product image wrappers already
 * are), which also fixes the aspect ratio so nothing shifts on load.
 */
export function ImageWithFallback({ src, alt, className, ...rest }: Props) {
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setFailed(false);
    setLoaded(false);
  }, [src]);

  const showFallback = failed || !src;

  return (
    <>
      {!loaded && !showFallback && (
        <div aria-hidden className="absolute inset-0 animate-pulse bg-taupe/20" />
      )}
      <img
        src={showFallback ? FALLBACK_IMAGE : src}
        alt={alt}
        loading="lazy"
        decoding="async"
        onLoad={() => setLoaded(true)}
        onError={() => setFailed(true)}
        className={cn("h-full w-full object-cover", className)}
        {...rest}
      />
    </>
  );
}
