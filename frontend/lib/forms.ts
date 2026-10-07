import type { FieldValues, Path, UseFormSetError } from "react-hook-form"
import { toast } from "sonner"

import { ApiError, errorMessage } from "@/lib/api"

/**
 * Show a failed request in a form: field-level details from the API go under their inputs,
 * the overall message goes to a toast.
 */
export function showFormError<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fields: readonly Path<T>[],
): void {
  if (error instanceof ApiError) {
    for (const detail of error.details) {
      const field = fields.find((name) => name === detail.field)
      if (field) {
        setError(field, { type: "server", message: detail.message })
      }
    }
  }
  toast.error(errorMessage(error))
}

/** Optional text input -> null when blank (the API stores NULL, not ""). */
export function blankToNull(value: string | undefined | null): string | null {
  const trimmed = value?.trim() ?? ""
  return trimmed === "" ? null : trimmed
}
