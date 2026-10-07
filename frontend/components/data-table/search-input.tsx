"use client"

import { Search } from "lucide-react"
import { useEffect, useState } from "react"

import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/use-debounce"

interface SearchInputProps {
  placeholder?: string
  onSearch: (value: string) => void
}

/** Search box that reports its value after the user stops typing. */
export function SearchInput({ placeholder = "Tìm kiếm...", onSearch }: SearchInputProps) {
  const [value, setValue] = useState("")
  const debounced = useDebouncedValue(value.trim())

  useEffect(() => {
    onSearch(debounced)
    // onSearch is recreated on every parent render; only the debounced value matters.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced])

  return (
    <div className="relative w-full sm:max-w-xs">
      <Search className="text-muted-foreground absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
      <Input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder={placeholder}
        className="pl-8"
        aria-label={placeholder}
      />
    </div>
  )
}
