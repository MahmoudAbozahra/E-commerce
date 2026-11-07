import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";

export function Pagination({ page, count, pageSize = 20, searchParams }: { page: number; count: number; pageSize?: number; searchParams: Record<string, string | undefined> }) {
  const pages = Math.ceil(count / pageSize);
  if (pages <= 1) return null;
  const hrefFor = (value: number) => {
    const query = new URLSearchParams(Object.entries(searchParams).filter((entry): entry is [string, string] => Boolean(entry[1])));
    query.set("page", String(value));
    return `?${query}`;
  };
  return <nav aria-label="Catalog pagination" className="mt-14 flex items-center justify-center gap-3"><Link aria-disabled={page <= 1} tabIndex={page <= 1 ? -1 : undefined} className="icon-button border border-ink/12 aria-disabled:pointer-events-none aria-disabled:opacity-30" href={hrefFor(Math.max(1, page - 1))}><ChevronLeft size={18}/><span className="sr-only">Previous page</span></Link><span className="text-sm text-ink/55">Page {page} of {pages}</span><Link aria-disabled={page >= pages} tabIndex={page >= pages ? -1 : undefined} className="icon-button border border-ink/12 aria-disabled:pointer-events-none aria-disabled:opacity-30" href={hrefFor(Math.min(pages, page + 1))}><ChevronRight size={18}/><span className="sr-only">Next page</span></Link></nav>;
}
