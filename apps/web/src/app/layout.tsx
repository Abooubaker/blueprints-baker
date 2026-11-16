import type { Metadata, Viewport } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "RoboCraft — AI robotics engineering copilot",
    template: "%s · RoboCraft",
  },
  description:
    "Describe the robot you want to build. RoboCraft turns it into a structured plan: components, wiring, code, mechanical assembly, and cost.",
  applicationName: "RoboCraft",
  keywords: ["robotics", "AI", "engineering", "Arduino", "ESP32", "Raspberry Pi"],
  authors: [{ name: "RoboCraft" }],
  openGraph: {
    title: "RoboCraft — AI robotics engineering copilot",
    description:
      "An AI-assisted workspace for designing, wiring, coding, and budgeting your first robot.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#06090a",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-canvas text-ink min-h-dvh antialiased">{children}</body>
    </html>
  );
}
