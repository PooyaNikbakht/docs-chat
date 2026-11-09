import Image from "next/image";
import photos from "@/data/photos.json";

export type PhotoName = keyof typeof photos;

/**
 * A pre-sized photo from public/photos. It fills its parent (which must be positioned and sized),
 * so layouts control the frame and the photo is cropped to cover it.
 */
export function Photo({
  name,
  alt,
  sizes,
  preload = false,
  className = "",
  position,
}: {
  name: PhotoName;
  alt: string;
  /** The rendered width at each breakpoint, so the browser picks the right file. */
  sizes: string;
  /** Only for the photo that is the largest thing above the fold. */
  preload?: boolean;
  className?: string;
  position?: string;
}) {
  return (
    <Image
      src={`/photos/${name}`}
      alt={alt}
      fill
      sizes={sizes}
      preload={preload}
      fetchPriority={preload ? "high" : undefined}
      className={`object-cover ${className}`}
      style={position ? { objectPosition: position } : undefined}
    />
  );
}

/** Coffee bean outlines, tiled. A quiet texture for flat colour bands. */
export function BeanPattern({ className = "", color = "currentColor" }: { className?: string; color?: string }) {
  return (
    <svg aria-hidden="true" focusable="false" className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}>
      <defs>
        <pattern id="nw-beans" width="72" height="72" patternUnits="userSpaceOnUse">
          <g fill="none" stroke={color} strokeWidth="1.4" strokeLinecap="round">
            <g transform="translate(18 20) rotate(-28)">
              <ellipse rx="8" ry="11.5" />
              <path d="M0 -10.5c-3 4-3 7 0 10.5s3 6.5 0 10.5" />
            </g>
            <g transform="translate(54 54) rotate(32)">
              <ellipse rx="8" ry="11.5" />
              <path d="M0 -10.5c-3 4-3 7 0 10.5s3 6.5 0 10.5" />
            </g>
          </g>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#nw-beans)" />
    </svg>
  );
}
