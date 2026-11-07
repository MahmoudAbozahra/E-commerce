import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  if (request.nextUrl.hostname === "127.0.0.1") {
    const canonical = request.nextUrl.clone();
    canonical.hostname = "localhost";
    return NextResponse.redirect(canonical);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|media|favicon.ico|robots.txt|sitemap.xml).*)"],
};
