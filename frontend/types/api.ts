/** Response envelopes of the EnergySmart API (see backend app/schemas/common.py). */

export interface ApiResponse<T> {
  success: true
  message: string
  data: T
}

export interface Pagination {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface PaginatedResponse<T> {
  success: true
  message: string
  data: T[]
  pagination: Pagination
}

export interface ErrorDetail {
  field: string | null
  message: string
}

export interface ErrorResponse {
  success: false
  message: string
  error: {
    code: string
    details?: ErrorDetail[]
  }
}

export type SortOrder = "asc" | "desc"

export interface ListParams {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: SortOrder
  [filter: string]: string | number | boolean | undefined
}
