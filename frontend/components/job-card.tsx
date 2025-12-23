"use client"

import { Job, api } from "@/lib/api"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CheckCircle2, Clock, PlayCircle, AlertTriangle, Download, ArrowRight, Sparkles } from "lucide-react"
import Link from "next/link"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const STATUS_ICONS = {
    queued: Clock,
    running: PlayCircle,
    completed: CheckCircle2,
    failed: AlertTriangle,
    cleaning: Sparkles,
}

const STATUS_COLORS = {
    queued: "text-yellow-500",
    running: "text-blue-500",
    completed: "text-green-500",
    failed: "text-red-500",
    cleaning: "text-purple-500",
}

export function JobCard({ job }: { job: Job }) {
    const Icon = STATUS_ICONS[job.status] || Clock
    const color = STATUS_COLORS[job.status] || "text-gray-500"

    // Infer "Healed" status if force_playwright was enabled in options (metadata)
    // We assume metadata has options if saved, or we check job.
    const isHealed = job.metadata?.options?.force_playwright === true

    return (
        <Card className="hover:shadow-lg transition-shadow border-muted/60 bg-card/50 backdrop-blur-sm">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="font-mono text-xs">{job.type.toUpperCase()}</Badge>
                    {isHealed && (
                        <Badge variant="secondary" className="bg-purple-500/10 text-purple-500 hover:bg-purple-500/20 shadow-sm border-purple-500/20">
                            <Sparkles className="w-3 h-3 mr-1" />
                            Healed
                        </Badge>
                    )}
                </div>
                <div className={color}>
                    <Icon className="w-5 h-5" />
                </div>
            </CardHeader>

            <CardContent>
                <CardTitle className="text-lg font-medium truncate" title={job.value}>
                    {job.value}
                </CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                    ID: <span className="font-mono">{job.id.slice(0, 8)}...</span>
                </p>
                <p className="text-xs text-muted-foreground mt-4">
                    {new Date(job.created_at).toLocaleString()}
                </p>
            </CardContent>

            <CardFooter className="flex justify-between pt-0">
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" disabled={job.status !== 'completed'}>
                            <Download className="w-4 h-4 mr-2" />
                            Export
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent>
                        <DropdownMenuItem asChild>
                            <a href={api.getDownloadUrl(job.id, 'csv')} target="_blank" rel="noopener noreferrer">CSV</a>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                            <a href={api.getDownloadUrl(job.id, 'json')} target="_blank" rel="noopener noreferrer">JSON</a>
                        </DropdownMenuItem>
                        <DropdownMenuItem asChild>
                            <a href={api.getDownloadUrl(job.id, 'sqlite')} target="_blank" rel="noopener noreferrer">SQLite</a>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>

                <Link href={`/jobs/${job.id}`}>
                    <Button size="sm" className="rounded-full">
                        Open <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                </Link>
            </CardFooter>
        </Card>
    )
}
