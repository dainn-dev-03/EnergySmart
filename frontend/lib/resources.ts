import { apiDelete, apiGet, apiList, apiPost, apiPut } from "@/lib/api"
import type { ListParams } from "@/types/api"
import type {
  Building,
  BuildingInput,
  ElectricityPrice,
  ElectricityUsage,
  ElectricityUsageInput,
  Floor,
  FloorInput,
  Meter,
  MeterInput,
  Room,
  RoomInput,
} from "@/types/models"

/** Typed client for one CRUD resource of the REST API. */
export interface Resource<T, TInput> {
  key: string
  list: (params?: ListParams) => ReturnType<typeof apiList<T>>
  get: (id: number) => Promise<T>
  create: (input: TInput) => ReturnType<typeof apiPost<T>>
  update: (id: number, input: TInput) => ReturnType<typeof apiPut<T>>
  remove: (id: number) => ReturnType<typeof apiDelete>
}

export function createResource<T, TInput>(path: string): Resource<T, TInput> {
  return {
    key: path,
    list: (params) => apiList<T>(path, params),
    get: (id) => apiGet<T>(`${path}/${id}`),
    create: (input) => apiPost<T>(path, input),
    update: (id, input) => apiPut<T>(`${path}/${id}`, input),
    remove: (id) => apiDelete(`${path}/${id}`),
  }
}

export const buildingsApi = createResource<Building, BuildingInput>("/buildings")
export const floorsApi = createResource<Floor, FloorInput>("/floors")
export const roomsApi = createResource<Room, RoomInput>("/rooms")
export const metersApi = createResource<Meter, MeterInput>("/meters")
export const usagesApi = createResource<ElectricityUsage, ElectricityUsageInput>(
  "/electricity-usages",
)
export const pricesApi = createResource<ElectricityPrice, Omit<ElectricityPrice, "id" | "created_at">>(
  "/electricity-prices",
)
