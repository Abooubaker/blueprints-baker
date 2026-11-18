import type { Metadata, Viewport } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Blueprints Baker — AI robotics engineering copilot",
    template: "%s · Blueprints Baker",
  },
  description:
    "Describe the robot you want to build. Blueprints Baker turns it into a structured plan: components, wiring, code, mechanical assembly, and cost.",
  applicationName: "Blueprints Baker",
  keywords: ["robotics", "AI", "engineering", "Arduino", "ESP32", "Raspberry Pi"],
  authors: [{ name: "Blueprints Baker" }],
  openGraph: {
    title: "Blueprints Baker — AI robotics engineering copilot",
    description:
      "An AI-assisted workspace for designing, wiring, coding, and budgeting your first robot.",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#07233d",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-canvas text-ink min-h-dvh antialiased">{children}</body>
    </html>
  );
}
