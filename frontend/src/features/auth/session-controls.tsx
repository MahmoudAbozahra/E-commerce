"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { LogOut, UserRound } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { clientApi } from "@/shared/api/client";
import type { User } from "@/shared/api/contracts";

export function SessionControls() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["session"],
    queryFn: () => clientApi<{ user: User }>("/api/auth/session"),
    retry: false,
  });

  if (!data?.user) {
    return (
      <Link href="/login" className="nav-pill" aria-label="Sign in">
        <UserRound size={17} aria-hidden="true" />
        <span className="hidden sm:inline">Sign in</span>
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-1">
      <Link href="/account" className="nav-pill">
        <UserRound size={17} aria-hidden="true" />
        <span className="hidden sm:inline">{data.user.first_name || data.user.username}</span>
      </Link>
      <button
        type="button"
        className="icon-button"
        aria-label="Sign out"
        onClick={async () => {
          await fetch("/api/auth/logout", { method: "POST" });
          queryClient.clear();
          router.push("/");
          router.refresh();
        }}
      >
        <LogOut size={17} aria-hidden="true" />
      </button>
    </div>
  );
}
