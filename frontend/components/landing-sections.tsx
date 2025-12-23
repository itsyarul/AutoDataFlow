"use client"

import { motion } from "framer-motion"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, Brain, Layers, BarChart3, Download, Sparkle } from "lucide-react"

import { InteractiveGradient } from "@/components/interactive-gradient"

export function FeaturesSection() {
    const features = [
        {
            icon: Brain,
            title: "AI & LLM Powered",
            description: "Generates cleaning scripts, heals broken selectors, and analyzes data using advanced LLMs.",
            color: "#c084fc" // Light Purple
        },
        {
            icon: Sparkle,
            title: "Prompt-Based Dataset Generation",
            description: "Describe your data needs in plain language—we generate the dataset for you.",
            color: "#c084fc"
        },
        {
            icon: Layers,
            title: "Deep Crawling",
            description: "Intelligent pagination following to extract data from multiple pages automatically.",
            color: "#c084fc"
        },
        {
            icon: BarChart3,
            title: "Data Analysis & Interactive Visualization",
            description: "Transform raw datasets into powerful insights through intelligent analytics and dynamic charts.",
            color: "#c084fc"
        },
        {
            icon: Shield,
            title: "Custom Proxy Support",
            description: "Configure personalized proxy routing to ensure anonymity and network control during scraping operations.",
            color: "#c084fc"
        },
        {
            icon: Download,
            title: "Flexible Data Export",
            description: "Export your data in multiple formats, including CSV, JSON, SQLite, and more—ready for any workflow.",
            color: "#c084fc"
        }
    ]

    return (
        <section className="py-12 md:py-24 bg-muted/20">
            <div className="container mx-auto px-4">
                <div className="text-center max-w-2xl mx-auto mb-16">
                    <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
                        Built for Modern Data Needs
                    </h2>
                    <p className="text-muted-foreground text-lg">
                        Stop writing brittle scrapers. Let AI handle the complexity while you focus on the insights.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {features.map((feature, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            viewport={{ once: true }}
                            className="h-full"
                        >
                            <InteractiveGradient
                                color={feature.color}
                                glowColor={feature.color}
                                className="h-full items-start text-left p-6"
                            >
                                <div className="flex flex-col items-start gap-4">
                                    <div className="p-2 rounded-lg bg-background/50 backdrop-blur-sm border border-white/10">
                                        <feature.icon style={{ color: feature.color }} className="w-8 h-8" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-xl mb-2">{feature.title}</h3>
                                        <p className="text-muted-foreground text-sm leading-relaxed">
                                            {feature.description}
                                        </p>
                                    </div>
                                </div>
                            </InteractiveGradient>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    )
}


export function UseCasesSection() {
    return (
        <section className="py-12 md:py-24">
            <div className="container mx-auto px-4">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Use Cases</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <motion.div
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        className="p-8 rounded-3xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20"
                    >
                        <h3 className="text-2xl font-bold mb-4">E-commerce Monitoring</h3>
                        <p className="text-muted-foreground mb-4">
                            Track prices, inventory levels, and product descriptions across thousands of SKUs in real-time.
                        </p>
                        <div className="h-40 bg-indigo-500/5 rounded-xl border border-indigo-500/10 flex items-center justify-center">
                            <span className="text-indigo-500 font-mono text-sm">{"{ price: 99.99, stock: 'In Stock' }"}</span>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, x: 50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        className="p-8 rounded-3xl bg-gradient-to-br from-orange-500/10 to-red-500/10 border border-orange-500/20"
                    >
                        <h3 className="text-2xl font-bold mb-4">Lead Generation</h3>
                        <p className="text-muted-foreground mb-4">
                            Extract contact details, company information, and social profiles from directories and lists.
                        </p>
                        <div className="h-40 bg-orange-500/5 rounded-xl border border-orange-500/10 flex items-center justify-center">
                            <span className="text-orange-500 font-mono text-sm">{"{ email: 'ceo@example.com' }"}</span>
                        </div>
                    </motion.div>
                </div>

            </div>
        </section>
    )
}

export function FAQSection() {
    const faqs = [
        {
            q: "Can I generate data just by describing it?",
            a: "Yes! With our 'Generative Database' feature, you simply describe the dataset you need (e.g., 'Generate a dataset of top 20 cars'), and our LLM engine creates it instantly—no scraping required."
        },
        {
            q: "How does the AI Data Analyst work?",
            a: "After data is collected, our built-in AI Analyst scans your dataset. It identifies trends, correlations, and key insights automatically, explaining them in plain English so you don't need to be a data scientist."
        },
        {
            q: "Can I visualize my data?",
            a: "Absolutely. The platform includes an interactive visualization engine that automatically generates charts and graphs relevant to your data structures."
        },
        {
            q: "Does it handle messy data?",
            a: "Yes. We offer an 'Auto-Clean' feature where the AI intelligently formats, standardizes, and corrects your data (e.g., fixing date formats, removing duplicates) before you export it."
        },
        {
            q: "What type of data can I extract?",
            a: "You can extract almost anything: HTML tables, product listings, article text, contact info, and dynamic content loaded via JavaScript. If it's visible on the web, we can likely structure it."
        },
        {
            q: "Is my data private?",
            a: "Yes. Your data remains completely private and secure. All uploaded, scraped, and generated datasets are processed only for your session and are never shared, reused, or exposed."
        },
        {
            q: "What export formats are supported?",
            a: "We support CSV, JSON, Parquet, and SQLite database exports out of the box."
        }
    ]

    return (
        <section className="py-12 md:py-24 bg-muted/20">
            <div className="container mx-auto px-4 max-w-3xl">
                <h2 className="text-3xl font-bold tracking-tight text-center mb-12">
                    Frequently Asked Questions
                </h2>
                <Accordion type="single" collapsible className="w-full">
                    {faqs.map((faq, idx) => (
                        <AccordionItem value={`item-${idx}`} key={idx}>
                            <AccordionTrigger className="text-left">{faq.q}</AccordionTrigger>
                            <AccordionContent className="text-muted-foreground">
                                {faq.a}
                            </AccordionContent>
                        </AccordionItem>
                    ))}
                </Accordion>
            </div>
        </section>
    )
}
