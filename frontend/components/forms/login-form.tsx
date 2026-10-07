"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useQueryClient } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { useRouter } from "next/navigation"
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
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle className="text-xl">Đăng nhập</CardTitle>
        <CardDescription>Nhập tài khoản để truy cập hệ thống</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} noValidate>
          <FieldGroup>
            <Controller
              name="username"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="username">Tên đăng nhập</FieldLabel>
                  <Input
                    {...field}
                    id="username"
                    autoComplete="username"
                    autoFocus
                    aria-invalid={fieldState.invalid}
                  />
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
                  <Input
                    {...field}
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    aria-invalid={fieldState.invalid}
                  />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
            <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
              Đăng nhập
            </Button>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  )
}
