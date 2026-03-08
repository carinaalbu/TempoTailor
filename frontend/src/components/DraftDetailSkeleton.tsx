import { Skeleton } from './ui/skeleton'

export function DraftDetailSkeleton() {
  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <Skeleton className="h-8 w-32" />
        <div className="flex gap-2">
          <Skeleton className="h-9 w-16 rounded-md" />
          <Skeleton className="h-9 w-16 rounded-md" />
        </div>
      </div>

      <div className="rounded-lg border border-white/10 p-6 mb-6">
        <Skeleton className="h-5 w-16 mb-4" />
        <Skeleton className="h-10 w-full rounded-md" />
      </div>

      <div className="rounded-lg border border-white/10 p-6 mb-6">
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4" />
      </div>

      <div className="rounded-lg border border-white/10 p-6 mb-6">
        <Skeleton className="h-5 w-24 mb-4" />
        <ul className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <li key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 w-6" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
              <Skeleton className="h-8 w-8 rounded-full" />
            </li>
          ))}
        </ul>
      </div>

      <div className="flex gap-4">
        <Skeleton className="h-9 w-28 rounded-md" />
        <Skeleton className="h-9 w-36 rounded-md" />
      </div>
    </div>
  )
}
