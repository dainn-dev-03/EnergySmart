"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { Loader2 } from "lucide-react"
import { useEffect } from "react"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useResourceMutations } from "@/hooks/use-resource"
import { blankToNull, showFormError } from "@/lib/forms"
import { buildingsApi } from "@/lib/resources"
import type { Building, BuildingInput } from "@/types/models"

const CODE_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.-]*$/

const buildingSchema = z.object({
  name: z.string().trim().min(1, "Vui lòng nhập tên tòa nhà").max(255, "Tối đa 255 ký tự"),
  code: z
    .string()
    .trim()
    .min(1, "Vui lòng nhập mã tòa nhà")
    .max(50, "Tối đa 50 ký tự")
    .regex(CODE_PATTERN, "Chỉ gồm chữ cái không dấu, chữ số và các ký tự - _ ."),
  address: z.string().max(500, "Tối đa 500 ký tự"),
  description: z.string(),
})

type BuildingValues = z.infer<typeof buildingSchema>
const FIELDS = ["name", "code", "address", "description"] as const

function toValues(building: Building | null): BuildingValues {
  return {
    name: building?.name ?? "",
    code: building?.code ?? "",
    address: building?.address ?? "",
    description: building?.description ?? "",
  }
}

function toInput(values: BuildingValues): BuildingInput {
  return {
    name: values.name,
    code: values.code.toUpperCase(),
    address: blankToNull(values.address),
    description: blankToNull(values.description),
  }
}

interface BuildingFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** null to create a new building. */
  building: Building | null
}

export function BuildingFormDialog({ open, onOpenChange, building }: BuildingFormDialogProps) {
  const { create, update } = useResourceMutations(buildingsApi)
  const form = useForm<BuildingValues>({
    resolver: zodResolver(buildingSchema),
    defaultValues: toValues(building),
  })

  useEffect(() => {
    if (open) form.reset(toValues(building))
  }, [open, building, form])

  const onSubmit = async (values: BuildingValues) => {
    try {
      const input = toInput(values)
      if (building) {
        await update.mutateAsync({ id: building.id, input })
      } else {
        await create.mutateAsync(input)
      }
      onOpenChange(false)
    } catch (error) {
      showFormError(error, form.setError, FIELDS)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{building ? "Cập nhật tòa nhà" : "Thêm tòa nhà"}</DialogTitle>
          <DialogDescription>Mã tòa nhà là duy nhất và được tự chuyển sang chữ in hoa.</DialogDescription>
        </DialogHeader>
        <form id="building-form" onSubmit={form.handleSubmit(onSubmit)} noValidate>
          <FieldGroup>
            <div className="grid gap-4 sm:grid-cols-[1fr_10rem]">
              <Controller
                name="name"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="building-name">Tên tòa nhà</FieldLabel>
                    <Input {...field} id="building-name" aria-invalid={fieldState.invalid} />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
              <Controller
                name="code"
                control={form.control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="building-code">Mã</FieldLabel>
                    <Input
                      {...field}
                      id="building-code"
                      placeholder="ES-01"
                      aria-invalid={fieldState.invalid}
                    />
                    <FieldError errors={[fieldState.error]} />
                  </Field>
                )}
              />
            </div>
            <Controller
              name="address"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="building-address">Địa chỉ</FieldLabel>
                  <Input {...field} id="building-address" aria-invalid={fieldState.invalid} />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
            <Controller
              name="description"
              control={form.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="building-description">Mô tả</FieldLabel>
                  <Textarea {...field} id="building-description" rows={3} />
                  <FieldError errors={[fieldState.error]} />
                </Field>
              )}
            />
          </FieldGroup>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="submit" form="building-form" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? <Loader2 className="animate-spin" /> : null}
            {building ? "Lưu thay đổi" : "Thêm mới"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
