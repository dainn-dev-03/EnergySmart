"use client"

import { Pencil, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"

interface RowActionsProps {
  onEdit: () => void
  onDelete: () => void
}

export function RowActions({ onEdit, onDelete }: RowActionsProps) {
  return (
    <div className="flex justify-end gap-1">
      <Button variant="ghost" size="icon-sm" onClick={onEdit} aria-label="Sửa">
        <Pencil />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onDelete}
        aria-label="Xóa"
        className="text-destructive hover:text-destructive"
      >
        <Trash2 />
      </Button>
    </div>
  )
}
