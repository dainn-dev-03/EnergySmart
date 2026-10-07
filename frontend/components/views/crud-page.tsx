"use client"

import { Plus } from "lucide-react"
import type { ReactNode } from "react"

import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"

interface CrudPageProps {
  title: string
  description: string
  createLabel: string
  canWrite: boolean
  onCreate: () => void
  toolbar: ReactNode
  children: ReactNode
  dialogs: ReactNode
  deleteDialog: {
    open: boolean
    title: string
    description: ReactNode
    isPending: boolean
    onCancel: () => void
    onConfirm: () => void
  }
}

/** Page frame of every CRUD screen: header + create button, filter row, list, dialogs. */
export function CrudPage({
  title,
  description,
  createLabel,
  canWrite,
  onCreate,
  toolbar,
  children,
  dialogs,
  deleteDialog,
}: CrudPageProps) {
  return (
    <div className="space-y-4">
      <PageHeader
        title={title}
        description={description}
        actions={
          canWrite ? (
            <Button onClick={onCreate}>
              <Plus />
              {createLabel}
            </Button>
          ) : null
        }
      />
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">{toolbar}</div>
      {children}
      {dialogs}
      <ConfirmDeleteDialog
        open={deleteDialog.open}
        onOpenChange={(open) => !open && deleteDialog.onCancel()}
        title={deleteDialog.title}
        description={deleteDialog.description}
        isPending={deleteDialog.isPending}
        onConfirm={deleteDialog.onConfirm}
      />
    </div>
  )
}
