import axios, { AxiosError } from "axios"

import { clearToken, getToken, redirectToLogin } from "@/lib/auth"
import type {
  ApiResponse,
  ErrorDetail,
  ErrorResponse,
  ListParams,
  PaginatedResponse,
} from "@/types/api"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

/** Error thrown for every failed request, carrying the backend's error envelope. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly details: ErrorDetail[] = [],
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export const http = axios.create({ baseURL: API_URL, timeout: 20_000 })

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponse>) => {
    const status = error.response?.status ?? 0
    const body = error.response?.data
    const isLoginRequest = error.config?.url?.includes("/auth/login") ?? false
    if (status === 401 && !isLoginRequest) {
      clearToken()
      redirectToLogin()
    }
    if (body && body.success === false) {
      return Promise.reject(
        new ApiError(body.message, status, body.error.code, body.error.details ?? []),
      )
    }
    const message =
      status === 0
        ? "Không kết nối được máy chủ. Kiểm tra backend đang chạy."
        : "Đã xảy ra lỗi không xác định"
    return Promise.reject(new ApiError(message, status, "NETWORK_ERROR"))
  },
)

/** Drop empty filters so they are not sent as `?search=`. */
function cleanParams(params?: ListParams): ListParams | undefined {
  if (!params) return undefined
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== ""),
  )
}

export async function apiGet<T>(url: string, params?: ListParams): Promise<T> {
  const { data } = await http.get<ApiResponse<T>>(url, { params: cleanParams(params) })
  return data.data
}

export async function apiList<T>(url: string, params?: ListParams): Promise<PaginatedResponse<T>> {
  const { data } = await http.get<PaginatedResponse<T>>(url, { params: cleanParams(params) })
  return data
}

export async function apiPost<T>(url: string, body?: unknown): Promise<ApiResponse<T>> {
  const { data } = await http.post<ApiResponse<T>>(url, body)
  return data
}

export async function apiPut<T>(url: string, body: unknown): Promise<ApiResponse<T>> {
  const { data } = await http.put<ApiResponse<T>>(url, body)
  return data
}

export async function apiDelete(url: string): Promise<ApiResponse<null>> {
  const { data } = await http.delete<ApiResponse<null>>(url)
  return data
}

/** Download a file endpoint (e.g. CSV export) using the auth header. */
export async function apiDownload(url: string, params?: ListParams): Promise<void> {
  const response = await http.get<Blob>(url, {
    params: cleanParams(params),
    responseType: "blob",
  })
  const disposition = String(response.headers["content-disposition"] ?? "")
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? "download"
  const link = document.createElement("a")
  link.href = URL.createObjectURL(response.data)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Đã xảy ra lỗi không xác định"
}
