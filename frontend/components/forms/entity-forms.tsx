"use client"

import { z } from "zod"

import { FormDialog } from "@/components/forms/form-dialog"
import { DateField, SelectField, TextareaField, TextField } from "@/components/forms/form-fields"
import { useEntityForm } from "@/hooks/use-entity-form"
import { useBuildingOptions, useFloorOptions, useMeterOptions, useRoomOptions } from "@/hooks/use-options"
import { todayInVietnam } from "@/lib/dates"
import { blankToNull } from "@/lib/forms"
import { toVietnamDateHour } from "@/lib/format"
import { HOUR_OPTIONS, METER_STATUS_OPTIONS, METER_TYPE_OPTIONS } from "@/lib/labels"
import {
  buildingsApi,
  floorsApi,
  metersApi,
  pricesApi,
  roomsApi,
  usagesApi,
} from "@/lib/resources"
import type {
  Building,
  ElectricityPrice,
  ElectricityUsage,
  Floor,
  Meter,
  MeterStatus,
  MeterType,
  Room,
} from "@/types/models"

/* ----- shared field rules (mirror the backend validation) ------------------------------------ */

const required = (label: string, max: number) =>
  z.string().trim().min(1, `Vui lòng nhập ${label}`).max(max, `Tối đa ${max} ký tự`)
const code = (label: string) =>
  required(label, 50).regex(
    /^[A-Za-z0-9][A-Za-z0-9_.-]*$/,
    "Chỉ gồm chữ cái không dấu, chữ số và các ký tự - _ .",
  )
const selected = (label: string) => z.string().min(1, `Vui lòng chọn ${label}`)
/** Accepts both "1,5" (Vietnamese decimal comma) and "1.5". */
const normalizeDecimal = (value: string) => value.trim().replace(",", ".")
const decimal = (places: number, message: string) =>
  z
    .string()
    .transform(normalizeDecimal)
    .refine((v) => v === "" || (!Number.isNaN(Number(v)) && Number(v) >= 0), message)
    .refine(
      (v) => v === "" || (v.split(".")[1]?.length ?? 0) <= places,
      `Tối đa ${places} chữ số thập phân`,
    )
const optionalNumber = (value: string): number | null =>
  value.trim() === "" ? null : Number(normalizeDecimal(value))
const today = todayInVietnam

interface DialogProps<T> {
  open: boolean
  onOpenChange: (open: boolean) => void
  entity: T | null
}

/* ----- Building ------------------------------------------------------------------------------ */

const buildingSchema = z.object({
  name: required("tên tòa nhà", 255),
  code: code("mã tòa nhà"),
  address: z.string().max(500, "Tối đa 500 ký tự"),
  description: z.string(),
})

export function BuildingFormDialog({ open, onOpenChange, entity }: DialogProps<Building>) {
  const { form, onSubmit, isSubmitting } = useEntityForm({
    schema: buildingSchema,
    resource: buildingsApi,
    entity,
    open,
    onOpenChange,
    toValues: (b) => ({
      name: b?.name ?? "",
      code: b?.code ?? "",
      address: b?.address ?? "",
      description: b?.description ?? "",
    }),
    toInput: (v) => ({
      name: v.name,
      code: v.code.toUpperCase(),
      address: blankToNull(v.address),
      description: blankToNull(v.description),
    }),
  })
  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={entity ? "Cập nhật tòa nhà" : "Thêm tòa nhà"}
      description="Mã tòa nhà là duy nhất và được tự chuyển sang chữ in hoa."
      isEditing={entity !== null}
      isSubmitting={isSubmitting}
      onSubmit={onSubmit}
    >
      <div className="grid gap-4 sm:grid-cols-[1fr_10rem]">
        <TextField control={form.control} name="name" label="Tên tòa nhà" />
        <TextField control={form.control} name="code" label="Mã" placeholder="ES-01" />
      </div>
      <TextField control={form.control} name="address" label="Địa chỉ" />
      <TextareaField control={form.control} name="description" label="Mô tả" />
    </FormDialog>
  )
}

/* ----- Floor --------------------------------------------------------------------------------- */

const floorSchema = z.object({
  building_id: selected("tòa nhà"),
  name: required("tên tầng", 100),
  floor_number: z
    .string()
    .trim()
    .regex(/^-?\d+$/, "Số tầng phải là số nguyên")
    .refine((v) => Number(v) >= -10 && Number(v) <= 200, "Số tầng từ -10 đến 200"),
  description: z.string(),
})

export function FloorFormDialog({ open, onOpenChange, entity }: DialogProps<Floor>) {
  const buildings = useBuildingOptions()
  const { form, onSubmit, isSubmitting } = useEntityForm({
    schema: floorSchema,
    resource: floorsApi,
    entity,
    open,
    onOpenChange,
    toValues: (f) => ({
      building_id: f ? String(f.building_id) : (buildings[0]?.value ?? ""),
      name: f?.name ?? "",
      floor_number: f ? String(f.floor_number) : "",
      description: f?.description ?? "",
    }),
    toInput: (v) => ({
      building_id: Number(v.building_id),
      name: v.name,
      floor_number: Number(v.floor_number),
      description: blankToNull(v.description),
    }),
  })
  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={entity ? "Cập nhật tầng" : "Thêm tầng"}
      description="Số tầng là duy nhất trong một tòa nhà (tầng hầm dùng số âm)."
      isEditing={entity !== null}
      isSubmitting={isSubmitting}
      onSubmit={onSubmit}
    >
      <SelectField control={form.control} name="building_id" label="Tòa nhà" options={buildings} />
      <div className="grid gap-4 sm:grid-cols-[1fr_8rem]">
        <TextField control={form.control} name="name" label="Tên tầng" placeholder="Tầng 3" />
        <TextField control={form.control} name="floor_number" label="Số tầng" inputMode="numeric" />
      </div>
      <TextareaField control={form.control} name="description" label="Mô tả" />
    </FormDialog>
  )
}

/* ----- Room ---------------------------------------------------------------------------------- */

const roomSchema = z.object({
  floor_id: selected("tầng"),
  name: required("tên phòng", 100),
  code: code("mã phòng"),
  area: decimal(2, "Diện tích phải là số dương"),
  description: z.string(),
})

export function RoomFormDialog({ open, onOpenChange, entity }: DialogProps<Room>) {
  const floors = useFloorOptions()
  const { form, onSubmit, isSubmitting } = useEntityForm({
    schema: roomSchema,
    resource: roomsApi,
    entity,
    open,
    onOpenChange,
    toValues: (r) => ({
      floor_id: r ? String(r.floor_id) : "",
      name: r?.name ?? "",
      code: r?.code ?? "",
      area: r?.area === null || r?.area === undefined ? "" : String(r.area),
      description: r?.description ?? "",
    }),
    toInput: (v) => ({
      floor_id: Number(v.floor_id),
      name: v.name,
      code: v.code.toUpperCase(),
      area: optionalNumber(v.area),
      description: blankToNull(v.description),
    }),
  })
  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={entity ? "Cập nhật phòng" : "Thêm phòng"}
      isEditing={entity !== null}
      isSubmitting={isSubmitting}
      onSubmit={onSubmit}
    >
      <SelectField control={form.control} name="floor_id" label="Tầng" options={floors} />
      <div className="grid gap-4 sm:grid-cols-[1fr_9rem]">
        <TextField control={form.control} name="name" label="Tên phòng" />
        <TextField control={form.control} name="code" label="Mã phòng" placeholder="R0301" />
      </div>
      <TextField control={form.control} name="area" label="Diện tích (m²)" inputMode="decimal" />
      <TextareaField control={form.control} name="description" label="Mô tả" />
    </FormDialog>
  )
}

/* ----- Meter --------------------------------------------------------------------------------- */

const meterSchema = z.object({
  room_id: selected("phòng"),
  meter_code: code("mã công tơ"),
  name: required("tên công tơ", 100),
  meter_type: selected("loại công tơ"),
  status: selected("trạng thái"),
  installation_date: z
    .string()
    .refine((v) => v === "" || v <= today(), "Ngày lắp đặt không được ở tương lai"),
})

export function MeterFormDialog({ open, onOpenChange, entity }: DialogProps<Meter>) {
  const rooms = useRoomOptions()
  const { form, onSubmit, isSubmitting } = useEntityForm({
    schema: meterSchema,
    resource: metersApi,
    entity,
    open,
    onOpenChange,
    toValues: (m) => ({
      room_id: m ? String(m.room_id) : "",
      meter_code: m?.meter_code ?? "",
      name: m?.name ?? "",
      meter_type: m?.meter_type ?? "SINGLE_PHASE",
      status: m?.status ?? "ACTIVE",
      installation_date: m?.installation_date ?? "",
    }),
    toInput: (v) => ({
      room_id: Number(v.room_id),
      meter_code: v.meter_code.toUpperCase(),
      name: v.name,
      meter_type: v.meter_type as MeterType,
      status: v.status as MeterStatus,
      installation_date: blankToNull(v.installation_date),
    }),
  })
  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={entity ? "Cập nhật công tơ" : "Thêm công tơ"}
      description="Xóa công tơ sẽ xóa luôn dữ liệu điện năng và cảnh báo của công tơ đó."
      isEditing={entity !== null}
      isSubmitting={isSubmitting}
      onSubmit={onSubmit}
    >
      <SelectField control={form.control} name="room_id" label="Phòng" options={rooms} />
      <div className="grid gap-4 sm:grid-cols-[9rem_1fr]">
        <TextField control={form.control} name="meter_code" label="Mã công tơ" placeholder="M051" />
        <TextField control={form.control} name="name" label="Tên công tơ" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField control={form.control} name="meter_type" label="Loại" options={METER_TYPE_OPTIONS} />
        <SelectField control={form.control} name="status" label="Trạng thái" options={METER_STATUS_OPTIONS} />
      </div>
      <DateField control={form.control} name="installation_date" label="Ngày lắp đặt" max={today()} clearable />
    </FormDialog>
  )
}

/* ----- Electricity usage --------------------------------------------------------------------- */

const usageSchema = z.object({
  meter_id: selected("công tơ"),
  date: z.string().min(1, "Vui lòng chọn ngày").refine((v) => v <= today(), "Không chọn ngày tương lai"),
  hour: selected("giờ"),
  kwh: decimal(3, "Điện năng phải là số không âm").refine((v) => v !== "", "Vui lòng nhập kWh"),
  voltage: decimal(2, "Điện áp phải là số không âm"),
  current: decimal(3, "Dòng điện phải là số không âm"),
  power_factor: decimal(3, "Hệ số công suất từ 0 đến 1").refine(
    (v) => v === "" || Number(v) <= 1,
    "Hệ số công suất từ 0 đến 1",
  ),
})

export function UsageFormDialog({ open, onOpenChange, entity }: DialogProps<ElectricityUsage>) {
  const meters = useMeterOptions()
  const { form, onSubmit, isSubmitting } = useEntityForm({
    schema: usageSchema,
    resource: usagesApi,
    entity,
    open,
    onOpenChange,
    toValues: (u) => {
      const local = u ? toVietnamDateHour(u.recorded_at) : { date: today(), hour: 0 }
      return {
        meter_id: u ? String(u.meter_id) : "",
        date: local.date,
        hour: String(local.hour),
        kwh: u ? String(u.kwh) : "",
        voltage: u?.voltage == null ? "" : String(u.voltage),
        current: u?.current == null ? "" : String(u.current),
        power_factor: u?.power_factor == null ? "" : String(u.power_factor),
      }
    },
    toInput: (v) => ({
      meter_id: Number(v.meter_id),
      // Hour start in Vietnam time; the API stores UTC.
      recorded_at: `${v.date}T${v.hour.padStart(2, "0")}:00:00+07:00`,
      kwh: Number(normalizeDecimal(v.kwh)),
      voltage: optionalNumber(v.voltage),
      current: optionalNumber(v.current),
      power_factor: optionalNumber(v.power_factor),
    }),
  })

  const hourValue = form.watch("hour")
  const hourNum = hourValue ? parseInt(hourValue, 10) : 0
  const hourHelper = `Dữ liệu áp dụng cho khoảng ${String(hourNum).padStart(2, "0")}:00 – ${String((hourNum + 1) % 24).padStart(2, "0")}:00`

  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={entity ? "Cập nhật dữ liệu điện" : "Ghi nhận dữ liệu điện"}
      description="Điện năng tiêu thụ trong 1 giờ. Chi phí được tự tính theo bảng giá có hiệu lực."
      isEditing={entity !== null}
      isSubmitting={isSubmitting}
      onSubmit={onSubmit}
    >
      <SelectField control={form.control} name="meter_id" label="Công tơ" options={meters} />
      <div className="grid gap-4 sm:grid-cols-2">
        <DateField control={form.control} name="date" label="Ngày" max={today()} />
        <SelectField 
          control={form.control} 
          name="hour" 
          label="Giờ bắt đầu" 
          options={HOUR_OPTIONS} 
          description={hourHelper}
        />
      </div>
      <TextField control={form.control} name="kwh" label="Điện năng (kWh)" inputMode="decimal" />
      <div className="grid gap-4 sm:grid-cols-3">
        <TextField control={form.control} name="voltage" label="Điện áp (V)" inputMode="decimal" />
        <TextField control={form.control} name="current" label="Dòng điện (A)" inputMode="decimal" />
        <TextField control={form.control} name="power_factor" label="Hệ số cosφ" inputMode="decimal" />
      </div>
    </FormDialog>
  )
}

/* ----- Electricity price --------------------------------------------------------------------- */

const priceSchema = z
  .object({
    name: required("tên bảng giá", 100),
    price_per_kwh: decimal(2, "Đơn giá phải là số dương").refine(
      (v) => v !== "" && Number(v) > 0,
      "Đơn giá phải lớn hơn 0",
    ),
    effective_from: z.string().min(1, "Vui lòng chọn ngày bắt đầu"),
    effective_to: z.string(),
  })
  .refine((v) => v.effective_to === "" || v.effective_to >= v.effective_from, {
    path: ["effective_to"],
    message: "Ngày kết thúc phải sau hoặc bằng ngày bắt đầu",
  })

export function PriceFormDialog({ open, onOpenChange, entity }: DialogProps<ElectricityPrice>) {
  const { form, onSubmit, isSubmitting } = useEntityForm({
    schema: priceSchema,
    resource: pricesApi,
    entity,
    open,
    onOpenChange,
    toValues: (p) => ({
      name: p?.name ?? "",
      price_per_kwh: p ? String(p.price_per_kwh) : "",
      effective_from: p?.effective_from ?? today(),
      effective_to: p?.effective_to ?? "",
    }),
    toInput: (v) => ({
      name: v.name,
      price_per_kwh: Number(normalizeDecimal(v.price_per_kwh)),
      effective_from: v.effective_from,
      effective_to: blankToNull(v.effective_to),
    }),
  })
  return (
    <FormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={entity ? "Cập nhật bảng giá" : "Thêm bảng giá điện"}
      description="Các khoảng hiệu lực không được chồng lên nhau. Để trống ngày kết thúc nếu đang áp dụng."
      isEditing={entity !== null}
      isSubmitting={isSubmitting}
      onSubmit={onSubmit}
    >
      <TextField control={form.control} name="name" label="Tên bảng giá" />
      <TextField control={form.control} name="price_per_kwh" label="Đơn giá (VND/kWh)" inputMode="decimal" />
      <div className="grid gap-4 sm:grid-cols-2">
        <DateField control={form.control} name="effective_from" label="Hiệu lực từ" />
        <DateField control={form.control} name="effective_to" label="Đến ngày" clearable />
      </div>
    </FormDialog>
  )
}
