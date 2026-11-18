import type { Metadata, Viewport } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Albayraq — AI robotics engineering copilot",
    template: "%s · Albayraq",
  },
  description:
    "Describe the robot you want to build. Albayraq identifies it, prices the parts at your stores, and generates the schematic, code, 3D print price, and documentation.",
  applicationName: "Albayraq",
  keywords: ["robotics", "AI", "engineering", "Arduino", "ESP32", "Raspberry Pi"],
  authors: [{ name: "Albayraq" }],
  openGraph: {
    title: "Albayraq — AI robotics engineering copilot",
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
