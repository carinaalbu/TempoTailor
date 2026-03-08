import { Skeleton } from './ui/skeleton'

export function AppShellSkeleton() {
  return (
    <div className="min-h-screen mesh-gradient text-white">
      <nav className="relative z-10 flex items-center justify-between px-6 py-5 md:px-10 lg:px-16">
        <Skeleton className="h-8 w-32" />
        <div className="flex items-center gap-4 md:gap-6">
          <Skeleton className="h-4 w-14" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-9 w-9 rounded-full" />
          <Skeleton className="h-9 w-24 rounded-full hidden sm:block" />
        </div>
      </nav>
      <main className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-4">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </main>
    </div>
  )
}
