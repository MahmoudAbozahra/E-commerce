"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { clientApi } from "@/shared/api/client";
import type { User } from "@/shared/api/contracts";
import { ApiError } from "@/shared/api/errors";
import { Button } from "@/shared/ui/button";
import { Field } from "@/shared/ui/field";

const loginSchema = z.object({ username: z.string().min(1, "Enter your username"), password: z.string().min(1, "Enter your password"), email: z.string(), first_name: z.string(), last_name: z.string() });
const registerSchema = loginSchema.superRefine((values, context) => {
  if (!z.email().safeParse(values.email).success) context.addIssue({ code: "custom", path: ["email"], message: "Enter a valid email" });
  if (!values.first_name) context.addIssue({ code: "custom", path: ["first_name"], message: "Enter your first name" });
  if (!values.last_name) context.addIssue({ code: "custom", path: ["last_name"], message: "Enter your last name" });
  if (values.password.length < 8) context.addIssue({ code: "custom", path: ["password"], message: "Use at least 8 characters" });
});
type Values = z.infer<typeof loginSchema>;

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const schema = mode === "login" ? loginSchema : registerSchema;
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<Values>({ resolver: zodResolver(schema), defaultValues: { username: "", password: "", email: "", first_name: "", last_name: "" } });

  async function submit(values: Values) {
    try {
      const user = await clientApi<User>(`/api/auth/${mode}`, { method: "POST", body: JSON.stringify(mode === "login" ? { username: values.username, password: values.password } : values) });
      queryClient.setQueryData(["session"], { user });
      const requested = searchParams.get("next");
      const destination = requested?.startsWith("/") && !requested.startsWith("//") ? requested : "/account";
      router.replace(destination);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError) {
        Object.entries(error.normalized.fields).forEach(([field, messages]) => {
          if (new Set(["username", "password", "email", "first_name", "last_name"]).has(field)) setError(field as keyof Values, { message: messages[0] });
        });
        setError("root", { message: error.normalized.message });
      } else setError("root", { message: "Could not reach the store. Please try again." });
    }
  }

  return (
    <form className="grid gap-5" onSubmit={handleSubmit(submit)} noValidate>
      {mode === "register" && <div className="grid gap-4 sm:grid-cols-2"><Field label="First name" autoComplete="given-name" error={errors.first_name?.message} {...register("first_name")}/><Field label="Last name" autoComplete="family-name" error={errors.last_name?.message} {...register("last_name")}/></div>}
      <Field label="Username" autoComplete="username" error={errors.username?.message} {...register("username")}/>
      {mode === "register" && (
        <Field label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")}/>
      )}
      <Field label="Password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} error={errors.password?.message} {...register("password")}/>
      {errors.root && <p role="alert" className="rounded-2xl bg-clay/8 p-4 text-sm text-clay">{errors.root.message}</p>}
      <Button type="submit" size="lg" disabled={isSubmitting}>{isSubmitting && <LoaderCircle className="animate-spin" size={17}/>} {mode === "login" ? "Sign in" : "Create account"}</Button>
      <p className="text-center text-sm text-ink/52">{mode === "login" ? <>New here? <Link className="font-semibold text-ink underline underline-offset-4" href="/register">Create an account</Link></> : <>Already have an account? <Link className="font-semibold text-ink underline underline-offset-4" href="/login">Sign in</Link></>}</p>
    </form>
  );
}
