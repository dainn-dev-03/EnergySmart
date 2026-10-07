"use client"

import { useQuery } from "@tanstack/react-query"

import type { Option } from "@/components/forms/form-fields"
import { buildingsApi, floorsApi, metersApi, roomsApi } from "@/lib/resources"

const MAX_OPTIONS = 100

/** Select options for parent entities. `undefined` parent id means "all". */
export function useBuildingOptions(): Option[] {
  const { data } = useQuery({
    queryKey: [buildingsApi.key, "options"],
    queryFn: () => buildingsApi.list({ page_size: MAX_OPTIONS, sort_by: "code" }),
  })
  return (data?.data ?? []).map((b) => ({ value: String(b.id), label: `${b.code} · ${b.name}` }))
}

export function useFloorOptions(buildingId?: number): Option[] {
  const { data } = useQuery({
    queryKey: [floorsApi.key, "options", buildingId],
    queryFn: () =>
      floorsApi.list({ page_size: MAX_OPTIONS, building_id: buildingId, sort_by: "floor_number" }),
  })
  return (data?.data ?? []).map((f) => ({ value: String(f.id), label: `${f.building.code} · ${f.name}` }))
}

export function useRoomOptions(floorId?: number): Option[] {
  const { data } = useQuery({
    queryKey: [roomsApi.key, "options", floorId],
    queryFn: () => roomsApi.list({ page_size: MAX_OPTIONS, floor_id: floorId, sort_by: "code" }),
  })
  return (data?.data ?? []).map((r) => ({ value: String(r.id), label: `${r.code} · ${r.name}` }))
}

export function useMeterOptions(floorId?: number): Option[] {
  const { data } = useQuery({
    queryKey: [metersApi.key, "options", floorId],
    queryFn: () =>
      metersApi.list({ page_size: MAX_OPTIONS, floor_id: floorId, sort_by: "meter_code" }),
  })
  return (data?.data ?? []).map((m) => ({
    value: String(m.id),
    label: `${m.meter_code} · ${m.room.name}`,
  }))
}
