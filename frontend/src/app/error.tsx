"use client";

import { Button } from "@/shared/ui/button";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <section className="narrow-shell py-28 text-center"><p className="eyebrow">Store connection</p><h1 className="section-title mt-4">We could not load this page.</h1><p className="mx-auto mt-5 max-w-lg text-ink/60">The catalog service may be unavailable. Your basket has not been changed.</p><Button className="mt-8" onClick={reset}>Try again</Button></section>;
}
