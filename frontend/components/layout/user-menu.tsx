"use client"

import { KeyRound, LogOut } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ROLE_LABELS, useCurrentUser } from "@/hooks/use-current-user"
import { logout } from "@/lib/auth"
import { apiPut } from "@/lib/api"

function initials(name: string): string {
  const words = name.trim().split(/\s+/)
  return words
    .slice(-2)
    .map((word) => word[0]?.toUpperCase() ?? "")
    .join("")
}

export function UserMenu() {
  const { data: user } = useCurrentUser()
  const [passwordOpen, setPasswordOpen] = useState(false)
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  if (!user) return null

  const displayName = user.full_name ?? user.username

  return (
    <>
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-10 gap-2 px-2">
          <Avatar className="size-8">
            <AvatarFallback>{initials(displayName)}</AvatarFallback>
          </Avatar>
          <span className="hidden text-left text-sm leading-tight sm:grid">
            <span className="font-medium">{displayName}</span>
            <span className="text-muted-foreground text-xs">{ROLE_LABELS[user.role]}</span>
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="space-y-1">
          <p className="font-medium">{displayName}</p>
          <p className="text-muted-foreground text-xs font-normal">{user.email}</p>
          <Badge variant="secondary">{ROLE_LABELS[user.role]}</Badge>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => setPasswordOpen(true)}>
          <KeyRound />
          Đổi mật khẩu
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={logout}>
          <LogOut />
          Đăng xuất
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
    <Dialog open={passwordOpen} onOpenChange={setPasswordOpen}><DialogContent><DialogHeader><DialogTitle>Đổi mật khẩu</DialogTitle></DialogHeader><div className="grid gap-3"><Input type="password" placeholder="Mật khẩu hiện tại" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} /><Input type="password" placeholder="Mật khẩu mới (ít nhất 8 ký tự)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} /><Button disabled={!currentPassword || newPassword.length < 8} onClick={async () => { try { await apiPut("/auth/me/password", { current_password: currentPassword, new_password: newPassword }); toast.success("Đổi mật khẩu thành công"); setPasswordOpen(false); setCurrentPassword(""); setNewPassword("") } catch (error) { toast.error(error instanceof Error ? error.message : "Không thể đổi mật khẩu") } }}>Lưu mật khẩu mới</Button></div></DialogContent></Dialog>
    </>
  )
}
