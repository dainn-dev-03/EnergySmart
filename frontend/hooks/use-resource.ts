"use client"

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"

import type { Resource } from "@/lib/resources"
import type { ListParams } from "@/types/api"

/** Paginated list of a resource; keeps the previous page visible while the next loads. */
export function useResourceList<T, TInput>(resource: Resource<T, TInput>, params: ListParams) {
  return useQuery({
    queryKey: [resource.key, "list", params],
    queryFn: () => resource.list(params),
    placeholderData: keepPreviousData,
  })
}

/**
 * Create / update / delete with success toast and cache invalidation.
 * Errors are left to the caller (forms map field errors under the inputs).
 */
export function useResourceMutations<T, TInput>(resource: Resource<T, TInput>) {
  const queryClient = useQueryClient()
  const onSuccess = ({ message }: { message: string }) => {
    toast.success(message)
    return queryClient.invalidateQueries({ queryKey: [resource.key] })
  }

  const create = useMutation({ mutationFn: resource.create, onSuccess })
  const update = useMutation({
    mutationFn: ({ id, input }: { id: number; input: TInput }) => resource.update(id, input),
    onSuccess,
  })
  const remove = useMutation({ mutationFn: resource.remove, onSuccess })
  return { create, update, remove }
}
