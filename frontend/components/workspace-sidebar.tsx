"use client"

import { useLocalStorage } from "@/hooks/use-local-storage"
import { useQueries } from "@tanstack/react-query"
import { api, Job } from "@/lib/api"
import { JobCard } from "@/components/job-card"
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { History, Loader2 } from "lucide-react"

export function WorkspaceSidebar() {
    const [myJobs] = useLocalStorage<string[]>('my_jobs', [])

    const jobQueries = useQueries({
        queries: myJobs.map((id) => ({
            queryKey: ['job', id],
            queryFn: () => api.getJob(id),
            refetchInterval: (query: any) => {
                const status = query.state.data?.status
                return (status === 'queued' || status === 'running') ? 5000 : false
            }
        }))
    })

    // Sort by created_at desc
    const jobs = jobQueries
        .map(q => q.data)
        .filter((j): j is Job => !!j)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    const isLoading = jobQueries.some(q => q.isLoading && !q.data)

    return (
        <Sheet>
            <SheetTrigger asChild>
                <Button
                    variant="outline"
                    size="sm"
                    className="fixed top-24 right-4 z-40 gap-2 bg-background/80 backdrop-blur-sm shadow-md border-border/50 hover:bg-background/90"
                >
                    <History className="w-4 h-4" />
                    <span className="hidden md:inline">My Workspace</span>
                    <span className="inline-flex items-center justify-center w-5 h-5 ml-1 text-xs font-bold text-primary-foreground bg-primary rounded-full">
                        {myJobs.length}
                    </span>
                </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-full sm:w-[400px] overflow-y-auto">
                <SheetHeader>
                    <SheetTitle>My Workspace</SheetTitle>
                    <SheetDescription>
                        Your recent scraping and generation tasks.
                    </SheetDescription>
                </SheetHeader>

                <div className="mt-8 space-y-4">
                    {jobs.length === 0 && !isLoading && (
                        <div className="text-center text-muted-foreground py-12">
                            No jobs yet. Start one!
                        </div>
                    )}

                    {jobs.map((job) => (
                        <div key={job.id} className="scale-90 origin-left w-[110%] -ml-1">
                            {/* Scale down JobCard slightly to fit narrow sidebar nicely if needed, or just let it flow */}
                            <JobCard job={job} />
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex justify-center p-4">
                            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
                        </div>
                    )}
                </div>
            </SheetContent>
        </Sheet>
    )
}
