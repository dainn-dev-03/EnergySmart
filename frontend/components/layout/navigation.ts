import {
  BellRing,
  ClipboardList,
  Building2,
  ChartLine,
  DoorOpen,
  FileText,
  Gauge,
  Layers,
  LayoutDashboard,
  Zap,
  type LucideIcon,
} from "lucide-react"

export interface NavItem {
  title: string
  href: string
  icon: LucideIcon
  description: string
}

export interface NavGroup {
  label: string
  items: NavItem[]
}

export const NAVIGATION: NavGroup[] = [
  {
    label: "Tổng quan",
    items: [
      {
        title: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
        description: "Tình hình tiêu thụ điện của tòa nhà",
      },
    ],
  },
  {
    label: "Quản lý",
    items: [
      { title: "Tòa nhà", href: "/buildings", icon: Building2, description: "Danh sách tòa nhà" },
      { title: "Tầng", href: "/floors", icon: Layers, description: "Các tầng của tòa nhà" },
      { title: "Phòng", href: "/rooms", icon: DoorOpen, description: "Phòng trong từng tầng" },
      { title: "Công tơ", href: "/meters", icon: Gauge, description: "Công tơ điện của các phòng" },
      {
        title: "Dữ liệu điện",
        href: "/electricity",
        icon: Zap,
        description: "Điện năng tiêu thụ theo giờ",
      },
    ],
  },
  {
    label: "Phân tích",
    items: [
      {
        title: "Phân tích",
        href: "/analytics",
        icon: ChartLine,
        description: "Xu hướng, giờ cao điểm, so sánh các kỳ",
      },
      {
        title: "Cảnh báo",
        href: "/alerts",
        icon: BellRing,
        description: "Tiêu thụ bất thường cần xử lý",
      },
      { title: "Báo cáo", href: "/reports", icon: FileText, description: "Báo cáo và xuất CSV" },
    ],
  },
  {
    label: "Quản trị",
    items: [
      {
        title: "Nhật ký hoạt động",
        href: "/audit-logs",
        icon: ClipboardList,
        description: "Lịch sử thao tác trong hệ thống",
      },
    ],
  },
]

export function findNavItem(pathname: string): NavItem | undefined {
  return NAVIGATION.flatMap((group) => group.items).find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  )
}
