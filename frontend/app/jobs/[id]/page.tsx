"use client"

import { useState, useEffect } from "react"

import { useParams } from "next/navigation"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { DataGrid } from "@/components/data-grid"
import { AIAnalyst } from "@/components/ai-analyst"
import { Download, Sparkles, ArrowLeft, RefreshCw, AlertTriangle } from "lucide-react"
import Link from "next/link"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

export default function JobDetailsPage() {
    const { id } = useParams() as { id: string }
    const queryClient = useQueryClient()
    const [selectedFile, setSelectedFile] = useState<string | null>(null)
    const [cleanInstruction, setCleanInstruction] = useState("")
    const [cleanFile, setCleanFile] = useState<string>("all")
    const [isCleanDialogOpen, setIsCleanDialogOpen] = useState(false)

    // Poll job status
    const { data: job, isLoading: jobLoading } = useQuery({
        queryKey: ['job', id],
        queryFn: () => api.getJob(id),
        refetchInterval: (query) => {
            const status = query.state.data?.status
            return (status === 'queued' || status === 'running' || status === 'cleaning') ? 1000 : false
        }
    })

    // Fetch available tables
    const { data: files } = useQuery({
        queryKey: ['job_files', id],
        queryFn: () => api.getJobTables(id),
        enabled: job?.status === 'completed',
    })

    // Auto-select first file
    useEffect(() => {
        if (files && files.length > 0 && !selectedFile) {
            setSelectedFile(files[0])
        }
    }, [files, selectedFile])

    // Fetch data for selected file
    const { data: jobData, isLoading: dataLoading } = useQuery({
        queryKey: ['job_data', id, selectedFile],
        queryFn: () => api.getJobData(id, selectedFile || undefined),
        enabled: job?.status === 'completed' && !!selectedFile,
    })

    const cleanMutation = useMutation({
        mutationFn: () => api.cleanJob(id, cleanInstruction, cleanFile === "all" ? undefined : cleanFile),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['job', id] })
            setIsCleanDialogOpen(false)
            alert("Cleaning started! Progress will update automatically.")
        },
        onError: () => alert("Failed to start cleaning")
    })

    if (jobLoading) {
        return <div className="flex h-screen items-center justify-center">Loading...</div>
    }

    if (!job) {
        return <div className="flex h-screen items-center justify-center">Job not found</div>
    }

    const isProcessing = job.status === 'queued' || job.status === 'running'
    const isCleaning = job.status === 'cleaning'
    const isFailed = job.status === 'failed'

    return (
        <div className="min-h-screen bg-background p-6">
            {/* Header */}
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center gap-4">
                    <Link href="/">
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="w-5 h-5" />
                        </Button>
                    </Link>
                    <div className="flex-1">
                        <div className="flex items-center gap-2">
                            <h1 className="text-2xl font-bold truncate max-w-xl">{job.value}</h1>
                            <Badge variant={
                                job.status === 'completed' ? 'default' :
                                    job.status === 'failed' ? 'destructive' : 'secondary'
                            }>
                                {job.status.toUpperCase()}
                            </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground font-mono mt-1">ID: {job.id}</p>
                    </div>

                    <div className="flex items-center gap-2">
                        {!isProcessing && !isFailed && (
                            <Dialog open={isCleanDialogOpen} onOpenChange={setIsCleanDialogOpen}>
                                <DialogTrigger asChild>
                                    <Button
                                        variant="default"
                                        className="gap-2 bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white border-0"
                                    >
                                        <Sparkles className="w-4 h-4" />
                                        Auto-Clean
                                    </Button>
                                </DialogTrigger>
                                <DialogContent className="sm:max-w-[425px]">
                                    <DialogHeader>
                                        <DialogTitle>Auto-Clean Settings</DialogTitle>
                                        <DialogDescription>
                                            Tell the AI how you want to clean your data. Leave empty for automatic cleaning.
                                        </DialogDescription>
                                    </DialogHeader>
                                    <div className="grid gap-4 py-4">
                                        <div className="grid gap-2">
                                            <Label htmlFor="file">Target File</Label>
                                            <Select value={cleanFile} onValueChange={setCleanFile}>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select file to clean" />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="all">All Files (Default)</SelectItem>
                                                    {files?.map((file) => (
                                                        <SelectItem key={file} value={file}>
                                                            {file}
                                                        </SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="grid gap-2">
                                            <Label htmlFor="instruction">Instructions (Optional)</Label>
                                            <Textarea
                                                id="instruction"
                                                placeholder="e.g. Remove rows where email is missing, convert price to number..."
                                                value={cleanInstruction}
                                                onChange={(e) => setCleanInstruction(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <DialogFooter>
                                        <Button
                                            type="submit"
                                            onClick={() => cleanMutation.mutate()}
                                            disabled={cleanMutation.isPending}
                                            className="bg-purple-600 hover:bg-purple-700 text-white"
                                        >
                                            {cleanMutation.isPending ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                                            Start Cleaning
                                        </Button>
                                    </DialogFooter>
                                </DialogContent>
                            </Dialog>
                        )}

                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="outline" className="gap-2">
                                    <Download className="w-4 h-4" /> Export
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                                <DropdownMenuItem asChild><a href={api.getDownloadUrl(id, 'csv')}>CSV</a></DropdownMenuItem>
                                <DropdownMenuItem asChild><a href={api.getDownloadUrl(id, 'json')}>JSON</a></DropdownMenuItem>
                                <DropdownMenuItem asChild><a href={api.getDownloadUrl(id, 'sqlite')}>SQLite</a></DropdownMenuItem>
                                <DropdownMenuItem asChild><a href={api.getDownloadUrl(id, 'parquet')}>Parquet</a></DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </div>

                {/* Progress Bar for processing */}
                {isProcessing && (
                    <div className="space-y-2 py-8 max-w-2xl mx-auto text-center">
                        <h3 className="tex-lg font-medium animate-pulse">Processing Job...</h3>
                        <Progress value={45} className="h-2 w-full animate-pulse" />
                        <p className="text-sm text-muted-foreground">The AI is scraping and analyzing content.</p>
                    </div>
                )}



                {/* Cool Cleaning Progress Bar */}
                {isCleaning && (
                    <div className="space-y-6 py-12 max-w-2xl mx-auto text-center relative overflow-hidden rounded-2xl border border-purple-500/20 bg-purple-500/5 p-8">
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/10 to-transparent animate-shimmer" />

                        <div className="relative z-10 flex flex-col items-center gap-4">
                            <div className="p-4 rounded-full bg-purple-500/10 animate-bounce">
                                <Sparkles className="w-8 h-8 text-purple-500" />
                            </div>
                            <h3 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600 animate-pulse">
                                AI Scrubbing in Progress...
                            </h3>
                            <p className="text-muted-foreground">Polishing your data and fixing errors.</p>

                            <div className="w-full max-w-md h-3 bg-secondary rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 animate-[progress_2s_ease-in-out_infinite] w-[80%]" />
                            </div>
                        </div>
                    </div>
                )}

                {isFailed && (
                    <div className="p-6 border border-destructive/20 bg-destructive/10 rounded-lg text-center space-y-2">
                        <AlertTriangle className="w-8 h-8 text-destructive mx-auto" />
                        <h3 className="font-semibold text-destructive">Job Failed</h3>
                        <p className="text-sm text-muted-foreground">Unable to process this request. Please try again with different settings.</p>
                    </div>
                )}

                {/* Main Content (Only when completed) */}
                {job.status === 'completed' && (
                    <Tabs defaultValue="data" className="space-y-6">
                        <TabsList className="bg-muted/50 p-1">
                            <TabsTrigger value="data">Data Preview</TabsTrigger>
                            <TabsTrigger value="analysis">AI Analyst</TabsTrigger>
                        </TabsList>

                        <TabsContent value="data" className="space-y-4">
                            {/* Table Selector */}
                            {files && files.length > 1 && (
                                <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
                                    <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">Tables:</span>
                                    {files.map((file) => (
                                        <Button
                                            key={file}
                                            variant={selectedFile === file ? "secondary" : "ghost"}
                                            size="sm"
                                            onClick={() => setSelectedFile(file)}
                                            className="whitespace-nowrap rounded-full border border-transparent hover:border-muted-foreground/20"
                                        >
                                            {file.replace(".csv", "").replace(/_/g, " ")}
                                        </Button>
                                    ))}
                                </div>
                            )}

                            {dataLoading ? (
                                <div className="h-64 flex items-center justify-center">Loading data...</div>
                            ) : (
                                <DataGrid data={jobData || []} />
                            )}
                        </TabsContent>

                        <TabsContent value="analysis">
                            <AIAnalyst jobId={id} />
                        </TabsContent>
                    </Tabs>
                )}
            </div>
        </div >
    )
}
