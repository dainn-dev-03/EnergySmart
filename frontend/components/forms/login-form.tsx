"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useQueryClient } from "@tanstack/react-query"
import { ArrowRight, Eye, EyeOff, Loader2, LockKeyhole, UserRound } from "lucide-react"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { CURRENT_USER_KEY } from "@/hooks/use-current-user"
import { apiPost } from "@/lib/api"
import { setToken } from "@/lib/auth"
import { showFormError } from "@/lib/forms"
import type { LoginResult } from "@/types/models"

const loginSchema = z.object({
  username: z.string().trim().min(1, "Vui lòng nhập tên đăng nhập"),
  password: z.string().min(1, "Vui lòng nhập mật khẩu"),
})

type LoginValues = z.infer<typeof loginSchema>

/** Only same-site paths are accepted as a post-login destination. */
function nextPath(): string {
  const next = new URLSearchParams(window.location.search).get("next")
  return next?.startsWith("/") && !next.startsWith("//") ? next : "/dashboard"
}

export function LoginForm() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [showPassword, setShowPassword] = useState(false)
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  })

  const onSubmit = async (values: LoginValues) => {
    try {
      const { data } = await apiPost<LoginResult>("/auth/login", values)
      setToken(data.access_token, data.expires_in)
      toast.dismiss() // drop errors of earlier attempts
      queryClient.setQueryData(CURRENT_USER_KEY, data.user)
      router.replace(nextPath())
    } catch (error) {
      showFormError(error, form.setError, ["username", "password"])
    }
  }

  return (
    <Card className="w-full border-border/70 bg-card shadow-xl shadow-[#214b3a]/10">
      <CardHeader className="space-y-2 pb-6 pt-8 text-left">
        <CardTitle className="text-2xl font-semibold">Chào mừng trở lại</CardTitle>
        <CardDescription className="text-sm">
          Đăng nhập bằng tài khoản EnergySmart của bạn.
        </CardDescription>
      </CardHeader>
      <CardContent className="pb-8">
        <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
          <FieldGroup>
            <Controller
              name="username"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="username">Tên đăng nhập</FieldLabel>
                  <div className="relative">
                    <UserRound className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                    <Input
                      {...field}
                      id="username"
                      autoComplete="username"
                      autoFocus
                      autoCapitalize="none"
                      spellCheck={false}
                      disabled={form.formState.isSubmitting}
                      className="h-11 pl-10"
                      aria-invalid={fieldState.invalid}
                    />
                  </div>
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
            <Controller
              name="password"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="password">Mật khẩu</FieldLabel>
                  <div className="relative">
                    <LockKeyhole className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden />
                    <Input
                      {...field}
                      id="password"
                      type={showPassword ? "text" : "password"}
                      autoComplete="current-password"
                      disabled={form.formState.isSubmitting}
                      className="h-11 pl-10 pr-11"
                      aria-invalid={fieldState.invalid}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      className="absolute top-1/2 right-2 -translate-y-1/2 text-muted-foreground"
                      aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                      aria-pressed={showPassword}
                      onClick={() => setShowPassword((visible) => !visible)}
                    >
                      {showPassword ? <EyeOff /> : <Eye />}
                    </Button>
                  </div>
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
            <Button type="submit" className="mt-2 h-11 w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : <ArrowRight />}
              {form.formState.isSubmitting ? "Đang đăng nhập" : "Đăng nhập"}
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  )
}
