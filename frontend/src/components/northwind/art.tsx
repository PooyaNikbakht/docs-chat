// Flat illustrations for the Northwind sample site. Solid fills only: no gradients, no shadows.
// Darker tones are the same colour under a flat black layer at low opacity.

const C = {
  espresso: "#3B2A20",
  roast: "#6B4A36",
  cream: "#F6F0E4",
  paper: "#FBF8F2",
  oat: "#ECE2CF",
  green: "#4F6B4A",
  sage: "#DFE6D6",
  sageDeep: "#B9C8AE",
  crema: "#C98B4E",
  sun: "#EBC89B",
  sea: "#AFC3BE",
  line: "#DCCFB8",
};

export function LogoMark({ size = 32, light = false }: { size?: number; light?: boolean }) {
  const disc = light ? C.cream : C.espresso;
  const needle = light ? C.espresso : C.paper;
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <circle cx="16" cy="16" r="16" fill={disc} />
      <path d="M16 5 L20.5 16 H11.5 Z" fill={needle} />
      <path d="M16 27 L11.5 16 H20.5 Z" fill={C.crema} />
      <circle cx="16" cy="16" r="1.8" fill={disc} />
    </svg>
  );
}

export function CoffeeBag({
  color,
  className,
  title,
}: {
  color: string;
  className?: string;
  title?: string;
}) {
  return (
    <svg
      viewBox="0 0 120 160"
      className={className}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
      focusable="false"
    >
      <CoffeeBagShape color={color} />
    </svg>
  );
}

export function Cup({ className, color = C.green }: { className?: string; color?: string }) {
  return (
    <svg viewBox="0 0 160 140" className={className} aria-hidden="true" focusable="false">
      <CupShape color={color} />
    </svg>
  );
}

function Bean({ x, y, r = 0, s = 1 }: { x: number; y: number; r?: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) rotate(${r}) scale(${s})`}>
      <ellipse cx="0" cy="0" rx="11" ry="7.5" fill={C.roast} />
      <path d="M-9 1 C-3 -4 3 4 9 -1" fill="none" stroke={C.espresso} strokeWidth="2" strokeLinecap="round" />
    </g>
  );
}

/** The home page hero: a harbour at the foot of green hills, with a bag and a cup up front. */
export function HeroScene({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 560 460"
      className={className}
      role="img"
      aria-label="Illustration: a bag of Harbour Blend and a cup of coffee in front of a harbour with a lighthouse and green hills."
    >
      <defs>
        <clipPath id="hero-clip">
          <rect width="560" height="460" rx="28" />
        </clipPath>
      </defs>
      <g clipPath="url(#hero-clip)">
        <rect width="560" height="460" fill={C.oat} />
        <circle cx="404" cy="118" r="62" fill={C.sun} />
        <path d="M0 236 C80 178 150 196 222 222 C300 250 360 176 448 182 C500 186 530 204 560 214 V320 H0 Z" fill={C.sageDeep} />
        <path d="M0 270 C70 240 140 250 210 268 C290 288 350 246 430 250 C490 253 530 266 560 274 V330 H0 Z" fill={C.green} />
        {/* Lighthouse on the far hill */}
        <g transform="translate(452 156)">
          <rect x="-7" y="10" width="14" height="44" fill={C.paper} />
          <rect x="-7" y="22" width="14" height="7" fill={C.crema} />
          <rect x="-7" y="38" width="14" height="7" fill={C.crema} />
          <rect x="-9" y="2" width="18" height="9" fill={C.espresso} />
          <path d="M-10 2 L0 -8 L10 2 Z" fill={C.espresso} />
        </g>
        <rect y="300" width="560" height="90" fill={C.sea} />
        <g stroke={C.paper} strokeWidth="3" strokeLinecap="round" opacity="0.7">
          <path d="M40 326 h46 M120 344 h34 M210 322 h52 M330 340 h40 M430 324 h56 M480 352 h30 M70 364 h28" />
        </g>
        {/* A small boat */}
        <g transform="translate(96 296)">
          <path d="M-26 0 H26 L18 12 H-18 Z" fill={C.espresso} />
          <path d="M0 -30 V0 M0 -30 L18 -4 H0" fill={C.paper} stroke={C.espresso} strokeWidth="2" />
        </g>
        <rect y="382" width="560" height="78" fill={C.cream} />
        <rect y="382" width="560" height="6" fill={C.line} />
        <g transform="translate(142 168) scale(1.48)">
          <CoffeeBagShape color="#8A5A3C" />
        </g>
        <g transform="translate(316 270)">
          <CupShape />
        </g>
        <Bean x={110} y={414} r={-20} />
        <Bean x={136} y={426} r={30} s={0.9} />
        <Bean x={482} y={420} r={10} />
        <Bean x={300} y={424} r={-35} s={0.85} />
      </g>
    </svg>
  );
}

// Inner shapes reused inside larger scenes (no wrapping <svg>).
function CoffeeBagShape({ color }: { color: string }) {
  return (
    <g>
      <path d="M14 22 H106 L110 146 Q110 152 104 152 H16 Q10 152 10 146 Z" fill={color} />
      <path d="M96 22 H106 L110 146 Q110 152 104 152 H100 Z" fill="#000" opacity="0.14" />
      <rect x="12" y="8" width="96" height="16" rx="2" fill={color} />
      <rect x="12" y="8" width="96" height="16" rx="2" fill="#000" opacity="0.22" />
      {[22, 32, 42, 52, 62, 72, 82, 92].map((x) => (
        <rect key={x} x={x} y="11" width="2" height="10" fill={C.paper} opacity="0.35" />
      ))}
      <circle cx="56" cy="40" r="4" fill="#000" opacity="0.2" />
      <rect x="24" y="58" width="64" height="66" rx="4" fill={C.paper} />
      <circle cx="56" cy="76" r="8" fill={C.espresso} />
      <path d="M56 70.5 L58.6 76 H53.4 Z" fill={C.paper} />
      <path d="M56 81.5 L53.4 76 H58.6 Z" fill={C.crema} />
      <rect x="34" y="92" width="44" height="5" rx="1" fill={C.espresso} />
      <rect x="40" y="102" width="32" height="3" rx="1" fill={color} />
      <rect x="44" y="110" width="24" height="3" rx="1" fill={C.line} />
    </g>
  );
}

function CupShape({ color = C.green }: { color?: string }) {
  return (
    <g>
      <g fill="none" stroke={C.roast} strokeWidth="4" strokeLinecap="round" opacity="0.5">
        <path d="M58 44 C50 34 66 26 58 14" />
        <path d="M78 44 C70 34 86 26 78 10" />
        <path d="M98 44 C90 34 106 26 98 14" />
      </g>
      <ellipse cx="80" cy="124" rx="64" ry="11" fill={C.line} />
      <ellipse cx="80" cy="121" rx="52" ry="7" fill={C.paper} />
      <path d="M118 70 h7 a15 15 0 0 1 0 30 h-7" fill="none" stroke={color} strokeWidth="9" />
      <path d="M32 58 H122 V94 Q122 120 94 120 H60 Q32 120 32 94 Z" fill={color} />
      <ellipse cx="77" cy="58" rx="45" ry="7" fill={C.espresso} />
      <ellipse cx="77" cy="58" rx="36" ry="4.5" fill={C.crema} />
    </g>
  );
}

/** Mountain ridges with a coffee branch: used for origins and sourcing. */
export function Origins({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 480 320"
      className={className}
      role="img"
      aria-label="Illustration: layered mountain ridges at sunrise with a coffee branch bearing red cherries."
    >
      <defs>
        <clipPath id="origins-clip">
          <rect width="480" height="320" rx="24" />
        </clipPath>
      </defs>
      <g clipPath="url(#origins-clip)">
        <rect width="480" height="320" fill={C.sage} />
        <circle cx="320" cy="96" r="44" fill={C.sun} />
        <path d="M0 210 L70 120 L120 170 L190 84 L270 186 L330 132 L400 196 L480 120 V320 H0 Z" fill={C.sageDeep} />
        <path d="M150 116 L190 84 L222 124 L204 118 L190 130 L172 116 Z" fill={C.paper} opacity="0.9" />
        <path d="M0 250 L90 176 L160 232 L250 160 L340 236 L410 190 L480 228 V320 H0 Z" fill={C.green} />
        <path d="M0 290 C90 262 180 280 260 270 C340 260 420 276 480 268 V320 H0 Z" fill={C.espresso} />
        {/* Coffee branch */}
        <g transform="translate(36 40)">
          <path d="M0 0 C40 30 70 70 92 132" fill="none" stroke={C.roast} strokeWidth="5" strokeLinecap="round" />
          {[
            [26, 22, -30],
            [52, 52, 20],
            [62, 78, -40],
            [80, 104, 25],
          ].map(([x, y, r], i) => (
            <g key={i} transform={`translate(${x} ${y}) rotate(${r})`}>
              <ellipse cx="22" cy="0" rx="24" ry="9" fill={C.green} />
              <path d="M0 0 H44" stroke={C.sage} strokeWidth="1.5" />
            </g>
          ))}
          {[
            [40, 40],
            [48, 46],
            [70, 90],
            [78, 84],
            [74, 96],
          ].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r="6.5" fill="#A63D2F" />
          ))}
        </g>
      </g>
    </svg>
  );
}

export function BrewIcon({ method, className }: { method: string; className?: string }) {
  const common = { className, "aria-hidden": true as const, focusable: "false" as const, viewBox: "0 0 120 120" };
  if (method === "Pour-over") {
    return (
      <svg {...common}>
        <rect x="0" y="0" width="120" height="120" rx="20" fill={C.sage} />
        <path d="M30 30 H90 L72 62 H48 Z" fill={C.paper} stroke={C.espresso} strokeWidth="4" strokeLinejoin="round" />
        <rect x="44" y="62" width="32" height="6" fill={C.espresso} />
        <path d="M60 70 v8" stroke={C.roast} strokeWidth="3" strokeLinecap="round" />
        <path d="M38 80 H82 L86 100 Q86 104 82 104 H38 Q34 104 34 100 Z" fill={C.green} />
        <rect x="40" y="88" width="40" height="12" rx="2" fill={C.espresso} opacity="0.55" />
      </svg>
    );
  }
  if (method === "French press") {
    return (
      <svg {...common}>
        <rect x="0" y="0" width="120" height="120" rx="20" fill={C.oat} />
        <rect x="56" y="14" width="8" height="14" rx="3" fill={C.espresso} />
        <rect x="58" y="26" width="4" height="26" fill={C.espresso} />
        <rect x="36" y="26" width="48" height="8" rx="3" fill={C.espresso} />
        <rect x="38" y="34" width="44" height="66" rx="4" fill={C.paper} stroke={C.espresso} strokeWidth="4" />
        <rect x="42" y="56" width="36" height="40" fill={C.roast} />
        <rect x="42" y="50" width="36" height="6" fill={C.espresso} />
        <path d="M82 46 h8 q6 0 6 6 v26 q0 6 -6 6 h-8" fill="none" stroke={C.espresso} strokeWidth="5" />
        <rect x="32" y="100" width="56" height="6" rx="3" fill={C.espresso} />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <rect x="0" y="0" width="120" height="120" rx="20" fill="#EFD9C2" />
      <ellipse cx="60" cy="94" rx="40" ry="8" fill={C.line} />
      <path d="M84 62 h4 a10 10 0 0 1 0 20 h-4" fill="none" stroke={C.espresso} strokeWidth="6" />
      <path d="M34 54 H86 V74 Q86 92 68 92 H52 Q34 92 34 74 Z" fill={C.espresso} />
      <ellipse cx="60" cy="54" rx="26" ry="5" fill={C.crema} />
      <g fill="none" stroke={C.roast} strokeWidth="3" strokeLinecap="round" opacity="0.6">
        <path d="M50 42 c-4 -6 4 -10 0 -16" />
        <path d="M66 42 c-4 -6 4 -10 0 -16" />
      </g>
    </svg>
  );
}

export function RoastMeter({ step, label }: { step: number; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5" aria-label={`Roast: ${label}`} role="img">
      {[1, 2, 3].map((i) => (
        <span
          key={i}
          aria-hidden="true"
          className={`h-2 w-2 rounded-full ${i <= step ? "bg-roast" : "border border-line bg-transparent"}`}
        />
      ))}
    </span>
  );
}
