import { Skeleton } from './ui/skeleton'

export function HistoryPageSkeleton() {
  return (
    <div className="min-h-screen mesh-gradient text-white">
      <div className="max-w-6xl mx-auto py-10 px-6 md:px-10">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-10">
          <Skeleton className="h-10 w-40" />
          <Skeleton className="h-12 w-32 rounded-full" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="h-full bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 p-5"
            >
              <Skeleton className="h-6 w-20 rounded-full mb-3" />
              <div className="flex items-center gap-2 mb-2">
                <Skeleton className="h-4 w-4 rounded-full" />
                <Skeleton className="h-4 w-24" />
              </div>
              <Skeleton className="h-6 w-3/4 mb-2" />
              <Skeleton className="h-4 w-full mb-1" />
              <Skeleton className="h-4 w-2/3 mb-3" />
              <Skeleton className="h-3 w-16 mb-4" />
              <div className="flex items-center gap-3 pt-3 border-t border-white/5">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-1.5 flex-1 rounded-full" />
                <Skeleton className="h-4 w-12" />
                <Skeleton className="h-5 w-5 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
