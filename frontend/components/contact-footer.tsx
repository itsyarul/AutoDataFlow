"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Github, Linkedin, Instagram, Send, Twitter } from "lucide-react"

export function ContactSection() {
    const [isSending, setIsSending] = useState(false)

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault()
        setIsSending(true)

        const formData = new FormData(e.currentTarget)
        const name = formData.get("name") as string
        const email = formData.get("email") as string
        const message = formData.get("message") as string

        const subject = `Project Inquiry from ${name}`
        const body = `Name: ${name}\nEmail: ${email}\n\nMessage:\n${message}`

        // Open default email client
        window.location.href = `mailto:yarulagarwal999@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`

        setIsSending(false)
    }

    return (
        <section className="py-24 relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/20 blur-[100px] rounded-full pointer-events-none" />

            <div className="container mx-auto px-4 relative z-10 max-w-xl">
                <div className="text-center mb-12">
                    <h2 className="text-3xl font-bold mb-4">Get in Touch</h2>
                    <p className="text-muted-foreground">Have a question or custom scraping requirement? Send us a message.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-4">
                        <div className="relative group">
                            <Input
                                name="name"
                                placeholder="Name"
                                className="bg-background/50 backdrop-blur-md border-muted focus:border-primary/50 focus:ring-primary/20 transition-all h-12"
                                required
                            />
                        </div>
                        <div className="relative group">
                            <Input
                                name="email"
                                type="email"
                                placeholder="Email"
                                className="bg-background/50 backdrop-blur-md border-muted focus:border-primary/50 focus:ring-primary/20 transition-all h-12"
                                required
                            />
                        </div>
                        <div className="relative group">
                            <Textarea
                                name="message"
                                placeholder="Your Message..."
                                className="bg-background/50 backdrop-blur-md border-muted focus:border-primary/50 focus:ring-primary/20 transition-all min-h-[150px]"
                                required
                            />
                        </div>
                    </div>

                    <div className="flex justify-center">
                        <motion.div
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                        >
                            <Button
                                size="lg"
                                className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-[0_0_20px_rgba(var(--primary),0.5)] hover:shadow-[0_0_30px_rgba(var(--primary),0.8)] transition-all duration-300"
                                disabled={isSending}
                            >
                                {isSending ? "Sending..." : (
                                    <>
                                        Send Message <Send className="ml-2 w-4 h-4" />
                                    </>
                                )}
                            </Button>
                        </motion.div>
                    </div>

                    <div className="flex justify-center gap-6 mt-12 pt-12 border-t border-muted/50">
                        <a href="https://github.com/itsyarul" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-white transition-colors">
                            <Github className="w-6 h-6" />
                        </a>
                        <a href="https://www.linkedin.com/in/yarul-agarwal-dataengineer" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-blue-400 transition-colors">
                            <Linkedin className="w-6 h-6" />
                        </a>
                        <a href="https://www.instagram.com/yarulllll?igsh=ODZnbGI0Y2EzcHl5" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-pink-500 transition-colors">
                            <Instagram className="w-6 h-6" />
                        </a>
                    </div>
                </form>
            </div>
        </section>
    )
}

export function Footer() {
    return (
        <footer className="bg-black/50 border-t border-white/10 py-12">
            <div className="container mx-auto px-4">
                <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="text-center md:text-left">
                        <h3 className="text-lg font-bold">AutoDataFlow</h3>
                        <p className="text-sm text-muted-foreground mt-2">© 2025 AI Data Systems. All rights reserved.</p>
                    </div>

                    <div className="flex gap-6">
                        <a href="https://www.instagram.com/yarulllll?igsh=ODZnbGI0Y2EzcHl5" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-pink-500 transition-colors flex items-center gap-2 text-sm">
                            <Instagram className="w-4 h-4" /> Instagram
                        </a>
                        <a href="https://www.linkedin.com/in/yarul-agarwal-dataengineer" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-blue-500 transition-colors flex items-center gap-2 text-sm">
                            <Linkedin className="w-4 h-4" /> LinkedIn
                        </a>
                    </div>
                </div>
            </div>
        </footer>
    )
}
