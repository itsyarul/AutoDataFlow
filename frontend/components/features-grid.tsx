"use client"

import { Bot, Monitor, Workflow, ArrowRight } from "lucide-react"
import { GlowingCards, GlowingCard } from "@/components/glowing-cards"

export function FeaturesGrid() {
    return (
        <div className="w-full max-w-7xl mx-auto">
            <div className="text-center mb-12 space-y-4">
                <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                    The ultimate data extraction platform
                </h2>
                <p className="text-muted-foreground text-lg">
                    Reliable and scalable data scraping so you can unlock the data you need.
                </p>
            </div>

            <GlowingCards gap="2rem">
                {/* Card 1: Extract (Purple) */}
                <GlowingCard glowColor="#a855f7" className="flex flex-col gap-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
                            <Bot className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-semibold">Extract</h3>
                    </div>

                    <div className="h-px w-full bg-border/50" />

                    <ul className="space-y-4 text-muted-foreground flex-1">
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-purple-500 flex-shrink-0" />
                            <span>AI-powered web scraper from any URL</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-purple-500 flex-shrink-0" />
                            <span>Generate actionable data using a single prompt</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-purple-500 flex-shrink-0" />
                            <span>Deep Scraping</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-purple-500 flex-shrink-0" />
                            <span>Handles pagination</span>
                        </li>
                    </ul>
                </GlowingCard>

                {/* Card 2: Monitor (Blue) */}
                <GlowingCard glowColor="#3b82f6" className="flex flex-col gap-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                            <Monitor className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-semibold">Monitor</h3>
                    </div>

                    <div className="h-px w-full bg-border/50" />

                    <ul className="space-y-4 text-muted-foreground flex-1">
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-blue-500 flex-shrink-0" />
                            <span>Advanced Data Preview UI</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-blue-500 flex-shrink-0" />
                            <span>Turn messy data into clean datasets</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-blue-500 flex-shrink-0" />
                            <span>Unlock insights from your data</span>
                        </li>
                    </ul>
                </GlowingCard>

                {/* Card 3: Export (Pink) */}
                <GlowingCard glowColor="#ec4899" className="flex flex-col gap-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-lg bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400">
                            <Workflow className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-semibold">Export</h3>
                    </div>

                    <div className="h-px w-full bg-border/50" />

                    <ul className="space-y-4 text-muted-foreground flex-1">
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-pink-500 flex-shrink-0" />
                            <span>CSV</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-pink-500 flex-shrink-0" />
                            <span>JSON</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-pink-500 flex-shrink-0" />
                            <span>SQlite</span>
                        </li>
                        <li className="flex items-start gap-2">
                            <ArrowRight className="w-4 h-4 mt-1 text-pink-500 flex-shrink-0" />
                            <span>Parquet</span>
                        </li>
                    </ul>
                </GlowingCard>
            </GlowingCards>
        </div>
    )
}
