/** Domain types mirroring the backend read schemas. Decimals arrive as JSON numbers. */

export type UserRole = "ADMIN" | "MANAGER" | "VIEWER"
export type MeterType = "SINGLE_PHASE" | "THREE_PHASE"
export type MeterStatus = "ACTIVE" | "INACTIVE" | "MAINTENANCE"
export type AlertSeverity = "INFO" | "WARNING" | "CRITICAL"

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserSummary {
  id: number
  username: string
  full_name: string | null
}

export interface AuditLog {
  id: number
  user_id: number | null
  action: string
  entity_type: string
  entity_id: number | null
  entity_label: string
  changes: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
  user: UserSummary | null
}

export interface LoginResult {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface BuildingRef {
  id: number
  name: string
  code: string
}

export interface Building extends BuildingRef {
  address: string | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface BuildingInput {
  name: string
  code: string
  address: string | null
  description: string | null
}

export interface FloorRef {
  id: number
  name: string
  floor_number: number
  building: BuildingRef
}

export interface Floor extends FloorRef {
  building_id: number
  description: string | null
  created_at: string
  updated_at: string
}

export interface FloorInput {
  building_id: number
  name: string
  floor_number: number
  description: string | null
}

export interface RoomRef {
  id: number
  name: string
  code: string
  floor: FloorRef
}

export interface Room extends RoomRef {
  floor_id: number
  area: number | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface RoomInput {
  floor_id: number
  name: string
  code: string
  area: number | null
  description: string | null
}

export interface MeterRef {
  id: number
  meter_code: string
  name: string
  room: RoomRef
}

export interface Meter extends MeterRef {
  room_id: number
  meter_type: MeterType
  status: MeterStatus
  installation_date: string | null
  created_at: string
  updated_at: string
}

export interface MeterInput {
  room_id: number
  meter_code: string
  name: string
  meter_type: MeterType
  status: MeterStatus
  installation_date: string | null
}

export interface ElectricityUsage {
  id: number
  meter_id: number
  recorded_at: string
  kwh: number
  voltage: number | null
  current: number | null
  power_factor: number | null
  cost: number
  created_at: string
  meter: MeterRef
}

export interface ElectricityUsageInput {
  meter_id: number
  recorded_at: string
  kwh: number
  voltage: number | null
  current: number | null
  power_factor: number | null
}

export interface ElectricityPrice {
  id: number
  name: string
  price_per_kwh: number
  effective_from: string
  effective_to: string | null
  created_at: string
}

export interface Alert {
  id: number
  meter_id: number
  alert_type: "HIGH_CONSUMPTION"
  severity: AlertSeverity
  message: string
  threshold_value: number | null
  actual_value: number | null
  usage_date: string
  is_resolved: boolean
  created_at: string
  resolved_at: string | null
  meter: MeterRef
}

export interface DashboardSummary {
  today_kwh: number
  month_kwh: number
  month_cost: number
  active_meters: number
  alert_count: number
}

export interface DailyPoint {
  date: string
  kwh: number
  cost: number
}

export interface MonthlyPoint {
  month: string
  kwh: number
  cost: number
}

export interface FloorTrend {
  floor_id: number
  floor_number: number
  floor_name: string
  kwh: number
  previous_kwh: number
  percentage_change: number | null
  status: "NORMAL" | "WARNING"
}

export interface FloorConsumption {
  floor_id: number
  floor_number: number
  floor_name: string
  kwh: number
  cost: number
  share_percent: number
}

export interface RoomConsumption {
  room_id: number
  room_code: string
  room_name: string
  floor_name: string
  kwh: number
  cost: number
  share_percent: number
}

export interface HourlyPoint {
  hour: number
  weekday_kwh: number
  weekend_kwh: number
}

export interface PeriodTotal {
  start: string
  end: string
  kwh: number
  cost: number
}

export interface Comparison {
  period: "day" | "week" | "month" | "custom"
  current_period: PeriodTotal
  previous_period: PeriodTotal
  difference: number
  percentage_change: number | null
  cost_difference: number
  cost_percentage_change: number | null
}

export type ReportGroup = "floor" | "room" | "meter"

export interface ReportRow {
  code: string
  name: string
  parent: string
  kwh: number
  cost: number
  share_percent: number
}

export interface ConsumptionReport {
  from_date: string
  to_date: string
  group_by: ReportGroup
  total_kwh: number
  total_cost: number
  rows: ReportRow[]
}
