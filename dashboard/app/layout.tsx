import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Doctrine Control Room",
  description:
    "Live Doctrine repository evidence, verification, state-chain integrity, and release identity.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
