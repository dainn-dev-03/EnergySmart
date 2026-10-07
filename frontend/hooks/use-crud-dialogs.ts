"use client"

import { useState } from "react"
import { toast } from "sonner"

import { useResourceMutations } from "@/hooks/use-resource"
import { errorMessage } from "@/lib/api"
import type { Resource } from "@/lib/resources"

/** Open/close state of the create-edit dialog and the delete confirmation of a CRUD page. */
export function useCrudDialogs<T extends { id: number }, TInput>(resource: Resource<T, TInput>) {
  const { remove } = useResourceMutations(resource)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<T | null>(null)
  const [deleting, setDeleting] = useState<T | null>(null)

  return {
    formOpen,
    setFormOpen,
    editing,
    deleting,
    isDeleting: remove.isPending,
    openCreate: () => {
      setEditing(null)
      setFormOpen(true)
    },
    openEdit: (entity: T) => {
      setEditing(entity)
      setFormOpen(true)
    },
    askDelete: (entity: T) => setDeleting(entity),
    cancelDelete: () => setDeleting(null),
    confirmDelete: () => {
      if (!deleting) return
      remove.mutate(deleting.id, {
        onSuccess: () => setDeleting(null),
        onError: (error) => toast.error(errorMessage(error)),
      })
    },
  }
}
