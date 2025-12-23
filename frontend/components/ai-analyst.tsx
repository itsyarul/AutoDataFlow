"use client"

import { useState, useEffect } from "react"
import dynamic from "next/dynamic"
import { Send, BarChart, Code2, AlertCircle } from "lucide-react"

// Dynamic import for Plotly to avoid SSR issues
const Plot = dynamic(() => import("react-plotly.js"), {
    ssr: false,
    loading: () => <div className="text-muted-foreground text-sm">Loading Chart Component...</div>
})
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useQuery } from "@tanstack/react-query"
import {
    ResizableHandle,
    ResizablePanel,
    ResizablePanelGroup,
} from "@/components/ui/resizable"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

interface ChatMessage {
    role: 'user' | 'assistant'
    content: string
    code?: string
    error?: boolean
}

interface AIAnalystProps {
    jobId: string
}

export function AIAnalyst({ jobId }: AIAnalystProps) {
    const [input, setInput] = useState("")
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [chartImage, setChartImage] = useState<string | null>(null)
    const [chartCode, setChartCode] = useState<string | null>(null)
    const [isChartLoading, setIsChartLoading] = useState(false)
    const [selectedFile, setSelectedFile] = useState<string | null>(null)
    const [chartData, setChartData] = useState<any>(null) // eslint-disable-line @typescript-eslint/no-explicit-any
    const [chartType, setChartType] = useState<'matplotlib' | 'plotly' | null>(null)

    // Fetch available tables
    const { data: files } = useQuery({
        queryKey: ['job_files', jobId],
        queryFn: () => api.getJobTables(jobId),
    })

    // Auto-select first file
    useEffect(() => {
        if (files && files.length > 0 && !selectedFile) {
            setSelectedFile(files[0])
        }
    }, [files, selectedFile])

    const handleSend = async () => {
        if (!input.trim()) return

        const query = input
        setInput("")
        setMessages(prev => [...prev, { role: 'user', content: query }])
        setIsLoading(true)

        try {
            // Pass selectedFile
            const res = await api.queryJob(jobId, query, selectedFile || undefined)

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: res.answer,
                code: res.code
            }])
        } catch (err: any) { // eslint-disable-line @typescript-eslint/no-explicit-any
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Sorry, I encountered an error analyzing the data.",
                error: true
            }])
        } finally {
            setIsLoading(false)
        }
    }

    const handleVisualize = async () => {
        if (!input.trim()) return
        const query = input
        setInput("")
        setMessages(prev => [...prev, { role: 'user', content: `Visualizing: ${query}` }])
        setIsChartLoading(true)

        try {
            // Pass selectedFile
            const res = await api.visualizeJob(jobId, query, undefined, selectedFile || undefined)

            if (res.type === 'plotly' && res.chart_data) {
                const parsedData = JSON.parse(res.chart_data)
                setChartData(parsedData)
                setChartType('plotly')
                setChartCode(res.code)
                setChartImage(null)
                setMessages(prev => [...prev, { role: 'assistant', content: "I've generated an interactive chart. Check the Visuals pane!" }])
            } else if (res.image_base64) {
                setChartImage(res.image_base64)
                setChartType('matplotlib')
                setChartCode(res.code)
                setChartData(null)
                setMessages(prev => [...prev, { role: 'assistant', content: "I've generated a chart. Check the Visuals pane!" }])
            } else if (res.error) {
                setMessages(prev => [...prev, { role: 'assistant', content: `Failed to generate chart: ${res.error}`, error: true }])
            }
        } catch (err) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Network error generating chart.", error: true }])
        } finally {
            setIsChartLoading(false)
        }
    }

    return (
        <div className="h-[600px] border rounded-xl overflow-hidden bg-card">
            <ResizablePanelGroup direction="horizontal">

                {/* Chat Pane */}
                <ResizablePanel defaultSize={40} minSize={30}>
                    <div className="flex flex-col h-full">
                        <div className="p-4 border-b bg-muted/30 font-medium flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                                <span className="flex h-2 w-2 rounded-full bg-green-500" />
                                AI Data Analyst
                            </div>

                            {/* Table Selector */}
                            {files && files.length > 0 && (
                                <select
                                    className="h-8 w-40 rounded-md border border-input bg-background px-2 py-1 text-xs ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    value={selectedFile || ""}
                                    onChange={(e) => setSelectedFile(e.target.value)}
                                >
                                    {files.map(f => (
                                        <option key={f} value={f}>
                                            {f.replace(".csv", "").replace(/_/g, " ")}
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>

                        <ScrollArea className="flex-1 p-4">
                            <div className="space-y-4">
                                {messages.length === 0 && (
                                    <div className="text-center text-muted-foreground py-10 text-sm">
                                        First select the table which you want to analyse or visualize.
                                        Ask questions like "What is the average price?" or "Show me a bar chart of categories".
                                        {selectedFile && <div className="mt-2 text-xs">Analyzing: <b>{selectedFile}</b></div>}
                                    </div>
                                )}
                                {messages.map((msg, i) => (
                                    <div key={i} className={cn(
                                        "flex flex-col max-w-[90%] rounded-lg p-3 text-sm",
                                        msg.role === 'user' ? "ml-auto bg-primary text-primary-foreground" : "bg-muted",
                                        msg.error && "bg-destructive/10 text-destructive border border-destructive/20"
                                    )}>
                                        <p className="whitespace-pre-wrap">{msg.content}</p>
                                        {msg.code && (
                                            <details className="mt-2 text-xs opacity-70 cursor-pointer">
                                                <summary className="hover:underline">View SQL/Python</summary>
                                                <pre className="mt-1 p-2 bg-black/10 rounded overflow-x-auto font-mono">
                                                    {msg.code}
                                                </pre>
                                            </details>
                                        )}
                                    </div>
                                ))}
                                {isLoading && (
                                    <div className="bg-muted w-fit rounded-lg p-3 text-sm animate-pulse">
                                        Thinking...
                                    </div>
                                )}
                            </div>
                        </ScrollArea>

                        <div className="p-4 border-t bg-background">
                            <div className="flex gap-2">
                                <Input
                                    placeholder={selectedFile ? `Ask about ${selectedFile}...` : "Ask about your data..."}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                                />
                                <Button size="icon" onClick={handleSend} disabled={isLoading || isChartLoading} title="Ask">
                                    <Send className="w-4 h-4" />
                                </Button>
                                <Button size="icon" variant="secondary" onClick={handleVisualize} disabled={isLoading || isChartLoading} title="Generate Chart">
                                    <BarChart className="w-4 h-4" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </ResizablePanel>

                <ResizableHandle />

                {/* Visuals Pane */}
                <ResizablePanel defaultSize={60}>
                    <div className="h-full bg-muted/10 flex flex-col">
                        <div className="p-4 border-b font-medium flex items-center justify-between bg-muted/30">
                            <span>Visuals</span>
                            {chartCode && (
                                <Button variant="ghost" size="sm" className="h-6 text-xs text-muted-foreground">
                                    <Code2 className="w-3 h-3 mr-1" /> View Code
                                </Button>
                            )}
                        </div>

                        <div className="flex-1 flex items-center justify-center p-6 relative overflow-hidden">
                            {isChartLoading ? (
                                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                                    <BarChart className="w-8 h-8 animate-bounce" />
                                    <span>Generating chart...</span>
                                </div>
                            ) : chartType === 'plotly' && chartData ? (
                                <div className="w-full h-full p-2">
                                    <Plot
                                        data={chartData.data}
                                        layout={{
                                            ...chartData.layout,
                                            autosize: true,
                                            margin: { l: 50, r: 20, t: 30, b: 50 },
                                            font: { family: 'inherit' },
                                            paper_bgcolor: 'rgba(0,0,0,0)',
                                            plot_bgcolor: 'rgba(0,0,0,0)',
                                        }}
                                        useResizeHandler={true}
                                        style={{ width: "100%", height: "100%" }}
                                        config={{ responsive: true, displayModeBar: true }}
                                    />
                                </div>
                            ) : chartType === 'matplotlib' && chartImage ? (
                                <img
                                    src={`data:image/png;base64,${chartImage}`}
                                    alt="Generated Chart"
                                    className="max-h-full max-w-full rounded-lg shadow-lg"
                                />
                            ) : (
                                <div className="text-muted-foreground flex flex-col items-center gap-2 opacity-50">
                                    <BarChart className="w-12 h-12" />
                                    <p>No visualization generated yet</p>
                                </div>
                            )}
                        </div>
                    </div>
                </ResizablePanel>

            </ResizablePanelGroup>
        </div>
    )
}
