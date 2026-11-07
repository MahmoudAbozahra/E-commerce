import type { NextConfig } from "next";

const apiUrl = new URL(process.env.DJANGO_API_URL ?? "http://127.0.0.1:8000");
const publicMediaOrigin = process.env.NEXT_PUBLIC_MEDIA_ORIGIN ? new URL(process.env.NEXT_PUBLIC_MEDIA_ORIGIN) : null;

const remotePatterns: NonNullable<NextConfig["images"]>["remotePatterns"] = [
  {
    protocol: apiUrl.protocol.replace(":", "") as "http" | "https",
    hostname: apiUrl.hostname,
    port: apiUrl.port,
    pathname: "/media/**",
  },
];

if (publicMediaOrigin) {
  remotePatterns.push({
    protocol: publicMediaOrigin.protocol.replace(":", "") as "http" | "https",
    hostname: publicMediaOrigin.hostname,
    port: publicMediaOrigin.port,
    pathname: "/**",
  });
}

const nextConfig: NextConfig = {
  // Allow the alternate local hosts developers use to open this dev server.
  // Otherwise Next rejects its own HMR websocket and repeatedly reconnects.
  allowedDevOrigins: ["127.0.0.1", "10.7.10.3"],
  images: {
    remotePatterns,
    dangerouslyAllowSVG: true,
    contentDispositionType: "attachment",
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
  async rewrites() {
    return [{ source: "/media/:path*", destination: `${apiUrl.origin}/media/:path*` }];
  },
};

export default nextConfig;
