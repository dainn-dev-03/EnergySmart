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

export interface ChatVisualization {
  summary?: {
    from_date: string | null
    to_date: string | null
    total_kwh: number
    total_cost: number
  }
  floors?: {
    items: {
      floor_number: number
      floor_name: string
      kwh: number
      cost: number
      share_percent: number
    }[]
  }
  rooms?: {
    items: {
      room_code: string
      room_name: string
      floor_name: string
      kwh: number
      cost: number
      share_percent: number
    }[]
  }
  hourly?: {
    items: {
      hour: number
      weekday_kwh: number
      weekend_kwh: number
    }[]
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

export async function apiStreamPost(
  url: string,
  body: unknown,
  onToken: (content: string) => void,
  onVisualization?: (visualization: ChatVisualization) => void,
): Promise<{ conversation_id: string }> {
  const token = getToken()
  const response = await fetch(
    `${API_URL.replace(/\/$/, "")}/${url.replace(/^\//, "")}`,
    {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    },
  )

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => null)) as ErrorResponse | null
    if (response.status === 401) {
      clearToken()
      redirectToLogin()
    }
    if (errorBody?.success === false) {
      throw new ApiError(
        errorBody.message,
        response.status,
        errorBody.error.code,
        errorBody.error.details ?? [],
      )
    }
    throw new ApiError(
      response.status === 0
        ? "Không kết nối được máy chủ. Kiểm tra backend đang chạy."
        : "Đã xảy ra lỗi không xác định",
      response.status,
      "NETWORK_ERROR",
    )
  }

  if (!response.body) {
    throw new ApiError("Máy chủ không trả về luồng dữ liệu.", response.status, "EMPTY_STREAM")
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let result: { conversation_id: string } | undefined

  async function consume(frame: string) {
    let event = ""
    const data: string[] = []
    for (const line of frame.split(/\r?\n/)) {
      if (line.startsWith("event:")) event = line.slice(6).trim()
      if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""))
    }
    if (!event || data.length === 0) return

    const payload: unknown = JSON.parse(data.join("\n"))
    if (typeof payload !== "object" || payload === null) {
      throw new ApiError("Dữ liệu trả về từ luồng chat không hợp lệ.", response.status, "INVALID_STREAM")
    }
    if (
      event === "token" &&
      "content" in payload &&
      typeof payload.content === "string"
    ) {
      onToken(payload.content)
    } else if (
      event === "visualization" &&
      "visualization" in payload &&
      typeof payload.visualization === "object" &&
      payload.visualization !== null
    ) {
      onVisualization?.(payload.visualization as ChatVisualization)
    } else if (
      event === "done" &&
      "conversation_id" in payload &&
      typeof payload.conversation_id === "string"
    ) {
      result = { conversation_id: payload.conversation_id }
    } else if (event === "error" && "message" in payload && typeof payload.message === "string") {
      throw new ApiError(
        payload.message,
        response.status,
        "code" in payload && typeof payload.code === "string" ? payload.code : "STREAM_ERROR",
      )
    } else {
      throw new ApiError("Dữ liệu trả về từ luồng chat không hợp lệ.", response.status, "INVALID_STREAM")
    }
  }

  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      const frames = buffer.split(/\r?\n\r?\n/)
      buffer = frames.pop() ?? ""
      for (const frame of frames) await consume(frame)
      if (done) break
    }
    if (buffer.trim()) await consume(buffer)
  } finally {
    reader.releaseLock()
  }

  if (!result) {
    throw new ApiError("Luồng chat kết thúc trước khi hoàn tất.", response.status, "INCOMPLETE_STREAM")
  }
  return result
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
