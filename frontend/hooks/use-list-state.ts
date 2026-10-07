"use client"

import { useState } from "react"

import type { ListParams, SortOrder } from "@/types/api"

export interface ListState {
  params: ListParams
  setPage: (page: number) => void
  setSearch: (search: string) => void
  setSort: (sortBy: string) => void
  setFilter: (name: string, value: string | number | undefined) => void
}

/** Pagination, search, sort and filters of a list page. Any change except paging resets to page 1. */
export function useListState(initial: ListParams = {}): ListState {
  const [params, setParams] = useState<ListParams>({ page: 1, page_size: 20, ...initial })

  return {
    params,
    setPage: (page) => setParams((current) => ({ ...current, page })),
    setSearch: (search) => setParams((current) => ({ ...current, search, page: 1 })),
    setSort: (sortBy) =>
      setParams((current) => {
        const sameColumn = current.sort_by === sortBy
        const order: SortOrder = sameColumn && current.sort_order === "asc" ? "desc" : "asc"
        return { ...current, sort_by: sortBy, sort_order: order, page: 1 }
      }),
    setFilter: (name, value) => setParams((current) => ({ ...current, [name]: value, page: 1 })),
  }
}
