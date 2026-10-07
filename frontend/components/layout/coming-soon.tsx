import { Construction } from "lucide-react"

import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent } from "@/components/ui/card"

/** Placeholder for modules whose screens are built in a later phase. */
export function ComingSoon({ title, description }: { title: string; description: string }) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />
      <Card>
        <CardContent className="text-muted-foreground flex flex-col items-center gap-3 py-16 text-center">
          <Construction className="size-10" />
          <p>Màn hình này đang được phát triển.</p>
        </CardContent>
      </Card>
    </div>
  )
}
