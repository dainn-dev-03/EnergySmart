"use client"

import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect } from "react"
import { useForm, type DefaultValues, type FieldValues, type Path } from "react-hook-form"
import type { z } from "zod"

import { useResourceMutations } from "@/hooks/use-resource"
import { showFormError } from "@/lib/forms"
import type { Resource } from "@/lib/resources"

interface EntityFormOptions<TValues extends FieldValues, TEntity, TInput> {
  schema: z.ZodType<TValues, TValues>
  resource: Resource<TEntity, TInput>
  entity: (TEntity & { id: number }) | null
  open: boolean
  onOpenChange: (open: boolean) => void
  toValues: (entity: TEntity | null) => TValues
  toInput: (values: TValues) => TInput
}

/**
 * Wiring shared by every create/edit dialog: zod validation, reset on open, create vs update,
 * server field errors under the inputs.
 */
export function useEntityForm<TValues extends FieldValues, TEntity, TInput>({
  schema,
  resource,
  entity,
  open,
  onOpenChange,
  toValues,
  toInput,
}: EntityFormOptions<TValues, TEntity, TInput>) {
  const { create, update } = useResourceMutations(resource)
  const form = useForm<TValues>({
    resolver: zodResolver(schema),
    defaultValues: toValues(entity) as DefaultValues<TValues>,
  })

  useEffect(() => {
    if (open) form.reset(toValues(entity))
    // toValues is a pure mapping defined next to the form; re-run only when the dialog opens.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, entity])

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const input = toInput(values)
      if (entity) {
        await update.mutateAsync({ id: entity.id, input })
      } else {
        await create.mutateAsync(input)
      }
      onOpenChange(false)
    } catch (error) {
      showFormError(error, form.setError, Object.keys(values) as Path<TValues>[])
    }
  })

  return { form, onSubmit, isSubmitting: form.formState.isSubmitting }
}
