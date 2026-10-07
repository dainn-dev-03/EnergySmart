"use client"

import { CircleCheck, CircleMinus, Wrench } from "lucide-react"

import { CrudList, Muted, withRowActions } from "@/components/data-table/crud-list"
import type { Column } from "@/components/data-table/data-table"
import { FilterSelect, toNumber } from "@/components/data-table/filter-select"
import { SearchInput } from "@/components/data-table/search-input"
import { MeterFormDialog } from "@/components/forms/entity-forms"
import { CrudPage } from "@/components/views/crud-page"
import { useCrudDialogs } from "@/hooks/use-crud-dialogs"
import { useCanWrite } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { useFloorOptions } from "@/hooks/use-options"
import { useResourceList } from "@/hooks/use-resource"
import { formatDate } from "@/lib/format"
import {
  METER_STATUS_LABELS,
  METER_STATUS_OPTIONS,
  METER_TYPE_LABELS,
  METER_TYPE_OPTIONS,
} from "@/lib/labels"
import { metersApi } from "@/lib/resources"
import type { Meter, MeterStatus } from "@/types/models"

const STATUS_ICON: Record<MeterStatus, { icon: typeof CircleCheck; className: string }> = {
  ACTIVE: { icon: CircleCheck, className: "text-status-good" },
  MAINTENANCE: { icon: Wrench, className: "text-status-serious" },
  INACTIVE: { icon: CircleMinus, className: "text-muted-foreground" },
}

function MeterStatusLabel({ status }: { status: MeterStatus }) {
  const { icon: Icon, className } = STATUS_ICON[status]
  return (
    <span className="inline-flex items-center gap-1.5 whitespace-nowrap">
      <Icon className={`size-4 ${className}`} aria-hidden />
      {METER_STATUS_LABELS[status]}
    </span>
  )
}

const COLUMNS: Column<Meter>[] = [
  {
    key: "meter_code",
    header: "Mã",
    sortKey: "meter_code",
    className: "w-24",
    cell: (m) => <span className="font-medium">{m.meter_code}</span>,
  },
  { key: "name", header: "Tên công tơ", sortKey: "name", cell: (m) => m.name },
  { key: "room", header: "Phòng", cell: (m) => `${m.room.code} · ${m.room.name}` },
  { key: "type", header: "Loại", className: "w-20", cell: (m) => METER_TYPE_LABELS[m.meter_type] },
  {
    key: "status",
    header: "Trạng thái",
    sortKey: "status",
    className: "w-40",
    cell: (m) => <MeterStatusLabel status={m.status} />,
  },
  {
    key: "installation_date",
    header: "Ngày lắp đặt",
    sortKey: "installation_date",
    className: "w-32",
    cell: (m) => (m.installation_date ? formatDate(m.installation_date) : <Muted />),
  },
]

export function MetersView() {
  const canWrite = useCanWrite()
  const floors = useFloorOptions()
  const list = useListState({ sort_by: "meter_code", sort_order: "asc" })
  const query = useResourceList(metersApi, list.params)
  const dialogs = useCrudDialogs(metersApi)

  return (
    <CrudPage
      title="Công tơ"
      description="Công tơ điện gắn với từng phòng"
      createLabel="Thêm công tơ"
      canWrite={canWrite}
      onCreate={dialogs.openCreate}
      toolbar={
        <>
          <SearchInput placeholder="Tìm theo mã, tên công tơ..." onSearch={list.setSearch} />
          <FilterSelect
            label="Tầng"
            value={list.params.floor_id as number | undefined}
            options={floors}
            onChange={(value) => list.setFilter("floor_id", toNumber(value))}
          />
          <FilterSelect
            label="Trạng thái"
            value={list.params.status as string | undefined}
            options={METER_STATUS_OPTIONS}
            onChange={(value) => list.setFilter("status", value)}
          />
          <FilterSelect
            label="Loại"
            value={list.params.meter_type as string | undefined}
            options={METER_TYPE_OPTIONS}
            onChange={(value) => list.setFilter("meter_type", value)}
            className="w-full sm:w-36"
          />
        </>
      }
      dialogs={
        <MeterFormDialog open={dialogs.formOpen} onOpenChange={dialogs.setFormOpen} entity={dialogs.editing} />
      }
      deleteDialog={{
        open: dialogs.deleting !== null,
        title: "Xóa công tơ?",
        description: (
          <>
            Công tơ <strong>{dialogs.deleting?.meter_code}</strong> cùng toàn bộ dữ liệu điện năng và cảnh
            báo của nó sẽ bị xóa vĩnh viễn.
          </>
        ),
        isPending: dialogs.isDeleting,
        onCancel: dialogs.cancelDelete,
        onConfirm: dialogs.confirmDelete,
      }}
    >
      <CrudList
        query={query}
        list={list}
        columns={withRowActions(COLUMNS, canWrite, dialogs.openEdit, dialogs.askDelete)}
        emptyMessage="Không có công tơ nào"
      />
    </CrudPage>
  )
}
