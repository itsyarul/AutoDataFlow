"use client"

import { useState, useEffect } from "react"
import { Search, Globe, Database, Settings, Play } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { JobRequest, JobOptions } from "@/lib/api"
import { cn } from "@/lib/utils"

interface MagicBarProps {
    onSubmit: (req: JobRequest) => void;
    isLoading?: boolean;
}

export function MagicBar({ onSubmit, isLoading }: MagicBarProps) {
    const [value, setValue] = useState("")
    const [mode, setMode] = useState<'url' | 'prompt'>('prompt')
    const [showAdvanced, setShowAdvanced] = useState(false)

    // Advanced Options State
    const [tableSelector, setTableSelector] = useState("")
    const [crawl, setCrawl] = useState(false)
    const [maxPages, setMaxPages] = useState(1)
    const [proxy, setProxy] = useState("")

    useEffect(() => {
        if (value.trim().startsWith("http")) {
            setMode("url")
        } else {
            setMode("prompt")
        }
    }, [value])

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!value.trim()) return

        const options: JobOptions = {
            force_playwright: true, // Defaulting to robust mode as per "Self Healing" flow logic
        }

        if (showAdvanced) {
            if (tableSelector) options.table_selector = tableSelector
            if (crawl) {
                options.crawl = true
                options.max_pages = maxPages
            }
            if (proxy) options.proxy = proxy
        }

        onSubmit({
            type: mode,
            value: value.trim(),
            options
        })
    }

    return (
        <div className="w-full max-w-3xl mx-auto space-y-4">
            <form onSubmit={handleSubmit} className="relative group">
                <div className="relative flex items-center">
                    <div className="absolute left-4 z-10 text-muted-foreground transition-colors group-focus-within:text-primary flex items-center justify-center">
                        {mode === 'url' ? <Globe className="w-5 h-5" /> : <img src="/adf-logo-round.png" alt="logo" className="w-8 h-8 object-contain" />}
                    </div>

                    <Input
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        placeholder="Paste a URL or describe a dataset..."
                        className="pl-14 pr-24 sm:pr-32 h-14 text-base sm:text-lg rounded-full shadow-lg border-2 border-transparent focus-visible:border-primary/50 transition-all bg-background/80 backdrop-blur-sm"
                    />

                    <div className="absolute right-2 flex items-center gap-2">
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className={cn("rounded-full px-2 sm:px-3", showAdvanced && "bg-secondary text-secondary-foreground")}
                        >
                            <Settings className="w-4 h-4 sm:mr-2" />
                            <span className="hidden sm:inline">Options</span>
                        </Button>
                        <Button
                            type="submit"
                            size="icon"
                            disabled={isLoading || !value.trim()}
                            className="rounded-full w-10 h-10"
                        >
                            {isLoading ? <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent" /> : <Play className="w-4 h-4 ml-0.5" />}
                        </Button>
                    </div>
                </div>
            </form>

            {/* Advanced Options Panel */}
            <div className={cn(
                "grid transition-all duration-300 ease-in-out overflow-hidden",
                showAdvanced ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
            )}>
                <div className="min-h-0">
                    <Card className="rounded-3xl border-muted bg-card/50 backdrop-blur-sm">
                        <CardContent className="p-6 grid gap-6 sm:grid-cols-2">

                            {/* Table Selector */}
                            <div className="space-y-2">
                                <Label>Table Selector (CSS)</Label>
                                <Input
                                    placeholder="e.g. table.price-list"
                                    value={tableSelector}
                                    onChange={(e) => setTableSelector(e.target.value)}
                                />
                            </div>

                            {/* Proxy */}
                            <div className="space-y-2">
                                <Label>Custom Proxy</Label>
                                <Input
                                    placeholder="http://user:pass@host:port"
                                    value={proxy}
                                    onChange={(e) => setProxy(e.target.value)}
                                />
                            </div>

                            {/* Crawl Toggle */}
                            <div className="flex items-center justify-between space-x-2 border rounded-xl p-3">
                                <Label className="flex flex-col">
                                    <span>Deep Crawl</span>
                                    <span className="font-normal text-xs text-muted-foreground">Follow pagination links</span>
                                </Label>
                                <Switch checked={crawl} onCheckedChange={setCrawl} />
                            </div>

                            {/* Max Pages (Only if Crawl is on) */}
                            <div className={cn("space-y-4 px-2", !crawl && "opacity-50 pointer-events-none")}>
                                <div className="flex justify-between">
                                    <Label>Max Pages</Label>
                                    <span className="text-sm text-muted-foreground">{maxPages}</span>
                                </div>
                                <Slider
                                    value={[maxPages]}
                                    onValueChange={(v) => setMaxPages(v[0])}
                                    min={1}
                                    max={50}
                                    step={1}
                                />
                            </div>

                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}
