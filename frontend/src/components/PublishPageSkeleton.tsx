import { Skeleton } from './ui/skeleton'

export function PublishPageSkeleton() {
  return (
    <div className="max-w-xl mx-auto py-12 px-4">
      <div className="rounded-lg border border-white/10 p-6">
        <Skeleton className="h-6 w-48 mb-6" />
        <div className="space-y-4">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
        <div className="flex gap-4 mt-6">
          <Skeleton className="h-10 w-36 rounded-md" />
          <Skeleton className="h-10 w-24 rounded-md" />
        </div>
      </div>
    </div>
  )
}
