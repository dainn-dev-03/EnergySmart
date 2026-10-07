"use client"

import { Plus } from "lucide-react"

import { ConfirmDeleteDialog } from "@/components/data-table/confirm-delete-dialog"
import { CrudList, Muted, withRowActions } from "@/components/data-table/crud-list"
import type { Column } from "@/components/data-table/data-table"
import { DateRangeFilter } from "@/components/data-table/date-range-filter"
import { FilterSelect, toNumber } from "@/components/data-table/filter-select"
import { PriceFormDialog, UsageFormDialog } from "@/components/forms/entity-forms"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useCrudDialogs } from "@/hooks/use-crud-dialogs"
import { useCanWrite, useIsAdmin } from "@/hooks/use-current-user"
import { useListState } from "@/hooks/use-list-state"
import { useFloorOptions, useMeterOptions } from "@/hooks/use-options"
import { useResourceList } from "@/hooks/use-resource"
import { formatDate, formatDateTime, formatKwh, formatNumber, formatVnd } from "@/lib/format"
import { pricesApi, usagesApi } from "@/lib/resources"
import type { ElectricityPrice, ElectricityUsage } from "@/types/models"

const USAGE_COLUMNS: Column<ElectricityUsage>[] = [
  {
    key: "recorded_at",
    header: "Thời điểm",
    sortKey: "recorded_at",
    className: "w-40",
    cell: (u) => <span className="tabular-nums">{formatDateTime(u.recorded_at)}</span>,
  },
  {
    key: "meter",
    header: "Công tơ",
    cell: (u) => (
      <div className="leading-tight">
        <p className="font-medium">{u.meter.meter_code}</p>
        <p className="text-muted-foreground text-xs">
          {u.meter.room.name} · {u.meter.room.floor.name}
        </p>
      </div>
    ),
  },
  {
    key: "kwh",
    header: "Điện năng",
    sortKey: "kwh",
    className: "text-right",
    cell: (u) => <span className="tabular-nums">{formatNumber(u.kwh, 3)} kWh</span>,
  },
  {
    key: "voltage",
    header: "Điện áp",
    className: "text-right",
    cell: (u) => (u.voltage === null ? <Muted /> : <span className="tabular-nums">{formatNumber(u.voltage, 1)} V</span>),
  },
  {
    key: "current",
    header: "Dòng điện",
    className: "text-right",
    cell: (u) => (u.current === null ? <Muted /> : <span className="tabular-nums">{formatNumber(u.current, 1)} A</span>),
  },
  {
    key: "power_factor",
    header: "cosφ",
    className: "text-right",
    cell: (u) => (u.power_factor === null ? <Muted /> : <span className="tabular-nums">{formatNumber(u.power_factor, 3)}</span>),
  },
  {
    key: "cost",
    header: "Chi phí",
    sortKey: "cost",
    className: "text-right",
    cell: (u) => <span className="tabular-nums">{formatVnd(u.cost)}</span>,
  },
]

const PRICE_COLUMNS: Column<ElectricityPrice>[] = [
  { key: "name", header: "Tên bảng giá", sortKey: "name", cell: (p) => <span className="font-medium">{p.name}</span> },
  {
    key: "price",
    header: "Đơn giá",
    sortKey: "price_per_kwh",
    className: "text-right",
    cell: (p) => <span className="tabular-nums">{formatVnd(p.price_per_kwh)}/kWh</span>,
  },
  {
    key: "effective_from",
    header: "Hiệu lực từ",
    sortKey: "effective_from",
    cell: (p) => formatDate(p.effective_from),
  },
  {
    key: "effective_to",
    header: "Đến ngày",
    cell: (p) => (p.effective_to ? formatDate(p.effective_to) : <Muted>Đang áp dụng</Muted>),
  },
]

function UsagesTab() {
  const canWrite = useCanWrite()
  const list = useListState({ sort_by: "recorded_at", sort_order: "desc" })
  const floorId = list.params.floor_id as number | undefined
  const floors = useFloorOptions()
  const meters = useMeterOptions(floorId)
  const query = useResourceList(usagesApi, list.params)
  const dialogs = useCrudDialogs(usagesApi)

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
        <FilterSelect
          label="Tầng"
          value={floorId}
          options={floors}
          onChange={(value) => {
            list.setFilter("meter_id", undefined)
            list.setFilter("floor_id", toNumber(value))
          }}
        />
        <FilterSelect
          label="Công tơ"
          value={list.params.meter_id as number | undefined}
          options={meters}
          onChange={(value) => list.setFilter("meter_id", toNumber(value))}
          className="w-full sm:w-56"
        />
        <DateRangeFilter
          from={list.params.from_date as string | undefined}
          to={list.params.to_date as string | undefined}
          onChange={({ from, to }) => {
            list.setFilter("from_date", from)
            list.setFilter("to_date", to)
          }}
        />
        {canWrite ? (
          <Button className="sm:ml-auto" onClick={dialogs.openCreate}>
            <Plus />
            Ghi nhận dữ liệu
          </Button>
        ) : null}
      </div>
      <CrudList
        query={query}
        list={list}
        columns={withRowActions(USAGE_COLUMNS, canWrite, dialogs.openEdit, dialogs.askDelete)}
        emptyMessage="Không có dữ liệu điện năng phù hợp"
      />
      <UsageFormDialog open={dialogs.formOpen} onOpenChange={dialogs.setFormOpen} entity={dialogs.editing} />
      <ConfirmDeleteDialog
        open={dialogs.deleting !== null}
        onOpenChange={(open) => !open && dialogs.cancelDelete()}
        title="Xóa bản ghi điện năng?"
        description={
          dialogs.deleting
            ? `Bản ghi ${formatKwh(dialogs.deleting.kwh)} của công tơ ${dialogs.deleting.meter.meter_code} lúc ${formatDateTime(dialogs.deleting.recorded_at)} sẽ bị xóa.`
            : ""
        }
        isPending={dialogs.isDeleting}
        onConfirm={dialogs.confirmDelete}
      />
    </div>
  )
}

function PricesTab() {
  const isAdmin = useIsAdmin()
  const list = useListState({ sort_by: "effective_from", sort_order: "desc" })
  const query = useResourceList(pricesApi, list.params)
  const dialogs = useCrudDialogs(pricesApi)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-muted-foreground text-sm">
          Chi phí của mỗi bản ghi = kWh × đơn giá có hiệu lực vào ngày ghi.
          {isAdmin ? "" : " Chỉ quản trị viên được thay đổi bảng giá."}
        </p>
        {isAdmin ? (
          <Button onClick={dialogs.openCreate}>
            <Plus />
            Thêm bảng giá
          </Button>
        ) : null}
      </div>
      <CrudList
        query={query}
        list={list}
        columns={withRowActions(PRICE_COLUMNS, isAdmin, dialogs.openEdit, dialogs.askDelete)}
        emptyMessage="Chưa có bảng giá điện"
      />
      <PriceFormDialog open={dialogs.formOpen} onOpenChange={dialogs.setFormOpen} entity={dialogs.editing} />
      <ConfirmDeleteDialog
        open={dialogs.deleting !== null}
        onOpenChange={(open) => !open && dialogs.cancelDelete()}
        title="Xóa bảng giá?"
        description="Chi phí đã ghi nhận không thay đổi, nhưng dữ liệu mới trong khoảng này sẽ không tính được chi phí."
        isPending={dialogs.isDeleting}
        onConfirm={dialogs.confirmDelete}
      />
    </div>
  )
}

export function ElectricityView() {
  return (
    <div className="space-y-4">
      <PageHeader
        title="Dữ liệu điện"
        description="Điện năng tiêu thụ theo từng giờ của các công tơ và bảng giá điện"
      />
      <Tabs defaultValue="usages">
        <TabsList>
          <TabsTrigger value="usages">Điện năng theo giờ</TabsTrigger>
          <TabsTrigger value="prices">Bảng giá điện</TabsTrigger>
        </TabsList>
        <TabsContent value="usages" className="mt-4">
          <UsagesTab />
        </TabsContent>
        <TabsContent value="prices" className="mt-4">
          <PricesTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
