// Lat/long grid over Vietnam's geographic extent (≈8.5–23.4°N, 102.1–109.5°E), 2° spacing.
const LATS = [8, 10, 12, 14, 16, 18, 20, 22, 24];
const LONS = [102, 104, 106, 108, 110];
const W = 400;
const H = 640;
const x = (lon: number) => ((lon - 102) / 8) * W;
const y = (lat: number) => H - ((lat - 8) / 16) * H;

export function Graticule({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox={`-40 -20 ${W + 80} ${H + 40}`}
      className={className}
      aria-hidden
      fill="none"
      preserveAspectRatio="xMidYMid slice"
    >
      <g stroke="currentColor" strokeWidth="0.75">
        {LATS.map((lat) => (
          <line key={`lat${lat}`} x1={0} x2={W} y1={y(lat)} y2={y(lat)} />
        ))}
        {LONS.map((lon) => (
          <line key={`lon${lon}`} x1={x(lon)} x2={x(lon)} y1={0} y2={H} />
        ))}
      </g>
      <g fill="currentColor" fontSize="11" fontFamily="var(--font-plex)">
        {LATS.map((lat) => (
          <text key={`tl${lat}`} x={-34} y={y(lat) + 4}>
            {lat}°N
          </text>
        ))}
        {LONS.map((lon) => (
          <text key={`tn${lon}`} x={x(lon) - 14} y={H + 16}>
            {lon}°E
          </text>
        ))}
      </g>
      {/* Hà Nội 21.03°N 105.85°E · TP. Hồ Chí Minh 10.78°N 106.70°E */}
      <g className="text-brass" fill="currentColor" fontSize="12" fontFamily="var(--font-plex)">
        <circle cx={x(105.85)} cy={y(21.03)} r="3" />
        <text x={x(105.85) + 8} y={y(21.03) + 4}>Hà Nội</text>
        <circle cx={x(106.7)} cy={y(10.78)} r="3" />
        <text x={x(106.7) + 8} y={y(10.78) + 4}>TP. Hồ Chí Minh</text>
      </g>
    </svg>
  );
}
