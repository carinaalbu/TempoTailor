import { Skeleton } from './ui/skeleton'

/** Shown while curating/generating playlist */
export function CreatePageSkeleton() {
  return (
    <div className="min-h-screen mesh-gradient text-white">
      <div className="max-w-xl mx-auto py-16 px-6">
        <div className="bg-white/[0.04] backdrop-blur-md rounded-2xl border border-white/10 p-8 md:p-10">
          <Skeleton className="h-8 w-64 mb-4" />
          <Skeleton className="h-4 w-48 mb-8" />

          <div className="space-y-6">
            <div>
              <Skeleton className="h-4 w-24 mb-4" />
              <Skeleton className="h-4 w-full mb-2" />
              <Skeleton className="h-4 w-32" />
            </div>
            <div>
              <Skeleton className="h-4 w-16 mb-4" />
              <Skeleton className="h-24 w-full rounded-xl" />
            </div>
            <Skeleton className="h-12 w-full rounded-full" />
          </div>

          <div className="mt-8 pt-8 border-t border-white/10">
            <p className="text-sm text-gray-400 mb-4">Curating your playlist...</p>
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
        </div>
      </div>
    </div>
  )
}
