"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { KeyRound, Plus, UserRoundCheck, UserRoundX } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useIsAdmin } from "@/hooks/use-current-user"
import { apiGet, apiPost } from "@/lib/api"
import type { User, UserRole } from "@/types/models"

const roles: UserRole[] = ["ADMIN", "MANAGER", "VIEWER"]

export function UsersView() {
  const isAdmin = useIsAdmin(); const client = useQueryClient(); const [open, setOpen] = useState(false); const [resetUser, setResetUser] = useState<User | null>(null); const [resetPassword, setResetPassword] = useState("")
  const [form, setForm] = useState({ username: "", email: "", full_name: "", password: "", role: "VIEWER" as UserRole })
  const users = useQuery({ queryKey: ["users"], queryFn: () => apiGet<User[]>("/users"), enabled: isAdmin })
  const create = useMutation({ mutationFn: () => apiPost<User>("/users", form), onSuccess: () => { toast.success("Tạo người dùng thành công"); client.invalidateQueries({ queryKey: ["users"] }); setOpen(false) } })
  const toggle = useMutation({ mutationFn: (user: User) => apiPost<User>(`/users/${user.id}/${user.is_active ? "deactivate" : "activate"}`), onSuccess: () => client.invalidateQueries({ queryKey: ["users"] }) })
  const reset = useMutation({ mutationFn: () => apiPost(`/users/${resetUser?.id}/reset-password`, { new_password: resetPassword }), onSuccess: () => { toast.success("Đặt lại mật khẩu thành công"); setResetUser(null); setResetPassword("") } })
  if (!isAdmin) return null
  return <div className="space-y-4"><PageHeader title="Người dùng" description="Quản lý tài khoản và phân quyền." actions={<Button onClick={() => setOpen(true)}><Plus />Thêm người dùng</Button>} />
    <div className="overflow-hidden rounded-lg border"><Table><TableHeader><TableRow><TableHead>Tên đăng nhập</TableHead><TableHead>Họ tên</TableHead><TableHead>Vai trò</TableHead><TableHead>Trạng thái</TableHead><TableHead /></TableRow></TableHeader><TableBody>{users.data?.map((user) => <TableRow key={user.id}><TableCell><p className="font-medium">{user.username}</p><p className="text-muted-foreground text-xs">{user.email}</p></TableCell><TableCell>{user.full_name ?? "—"}</TableCell><TableCell><Badge variant="secondary">{user.role}</Badge></TableCell><TableCell>{user.is_active ? "Hoạt động" : "Đã khóa"}</TableCell><TableCell className="flex justify-end gap-2"><Button variant="outline" size="sm" onClick={() => setResetUser(user)}><KeyRound />Đặt lại MK</Button><Button variant="outline" size="sm" onClick={() => toggle.mutate(user)}>{user.is_active ? <UserRoundX /> : <UserRoundCheck />}{user.is_active ? "Khóa" : "Mở khóa"}</Button></TableCell></TableRow>)}</TableBody></Table></div>
    <Dialog open={open} onOpenChange={setOpen}><DialogContent><DialogHeader><DialogTitle>Thêm người dùng</DialogTitle></DialogHeader><div className="grid gap-3"><Input placeholder="Tên đăng nhập" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })}/><Input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}/><Input placeholder="Họ và tên" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}/><Input type="password" placeholder="Mật khẩu (ít nhất 8 ký tự)" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}/><Select value={form.role} onValueChange={(role) => setForm({ ...form, role: role as UserRole })}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent>{roles.map((role) => <SelectItem key={role} value={role}>{role}</SelectItem>)}</SelectContent></Select><Button disabled={create.isPending || form.password.length < 8} onClick={() => create.mutate()}>Tạo tài khoản</Button></div></DialogContent></Dialog>
    <Dialog open={resetUser !== null} onOpenChange={(value) => !value && setResetUser(null)}><DialogContent><DialogHeader><DialogTitle>Đặt lại mật khẩu</DialogTitle></DialogHeader><div className="grid gap-3"><p className="text-muted-foreground text-sm">Tài khoản: <strong>{resetUser?.username}</strong></p><Input type="password" placeholder="Mật khẩu mới (ít nhất 8 ký tự)" value={resetPassword} onChange={(e) => setResetPassword(e.target.value)} /><Button disabled={reset.isPending || resetPassword.length < 8} onClick={() => reset.mutate()}>Đặt lại mật khẩu</Button></div></DialogContent></Dialog>
  </div>
}
