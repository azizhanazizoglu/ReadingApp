import * as React from "react";

export const AllianzLogo = ({
  className = "h-9 w-9",
  darkMode = false,
}: { className?: string; darkMode?: boolean }) => (
  <svg
    className={className}
    viewBox="0 0 320 320"
    fill="none"
    aria-label="Allianz Logo"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      cx="160"
      cy="160"
      r="150"
      fill={darkMode ? "#fff" : "#0057A0"}
      stroke="#0057A0"
      strokeWidth="20"
    />
    <g>
      <rect
        x="85"
        y="110"
        width="40"
        height="100"
        rx="12"
        fill={darkMode ? "#0057A0" : "#fff"}
      />
      <rect
        x="140"
        y="80"
        width="40"
        height="130"
        rx="12"
        fill={darkMode ? "#0057A0" : "#fff"}
      />
      <rect
        x="195"
        y="110"
        width="40"
        height="100"
        rx="12"
        fill={darkMode ? "#0057A0" : "#fff"}
      />
    </g>
  </svg>
);