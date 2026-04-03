import "./globals.css";
import type { Metadata } from "next";
import { QueryProvider } from "../components/query-provider";

export const metadata: Metadata = {
  title: "RGP",
  description: "Request Governance Platform"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
