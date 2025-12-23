"use client"

import { useRouter } from "next/navigation"
import { useMutation } from "@tanstack/react-query"
import { HeroSection } from "@/components/hero-section"
import { MagicBar } from "@/components/magic-bar"
import { api, JobRequest } from "@/lib/api"
import { SmoothScroll } from "@/components/smooth-scroll"
import { FeaturesSection, FAQSection } from "@/components/landing-sections"
import { ContactSection, Footer } from "@/components/contact-footer"
import { FeaturesGrid } from "@/components/features-grid"
import { WorkspaceSidebar } from "@/components/workspace-sidebar"

export default function Dashboard() {
  const router = useRouter()
  // Data logic moved to WorkspaceSidebar

  const createJobMutation = useMutation({
    mutationFn: (req: JobRequest) => api.createJob(req),
    onSuccess: (data) => {
      // We need to update local storage so Sidebar sees it?
      // useLocalStorage hooks sync via 'storage' event across tabs, but in same component?
      // The Sidebar uses useLocalStorage('my_jobs'), so we should update it here too OR let Sidebar handle it?
      // Wait, Sidebar reads "my_jobs". If we write to "my_jobs" here, Sidebar will react if we use the SAME hook.
      // So we DO need to keep the writer logic here.

      // Quick fix: Read existing, append, write.
      const existing = JSON.parse(localStorage.getItem('my_jobs') || '[]')
      localStorage.setItem('my_jobs', JSON.stringify([data.job_id, ...existing]))
      // Trigger storage event for other hooks
      window.dispatchEvent(new Event('storage'))

      router.push(`/jobs/${data.job_id}`)
    },
    onError: (error) => {
      console.error(error)
      alert("Failed to create job")
    }
  })

  return (
    <SmoothScroll>
      <main className="min-h-screen bg-background text-foreground">

        {/* Brand Logo */}
        <div className="absolute top-6 left-6 z-50 pointer-events-auto">
          <img
            src="/logo.png"
            alt="AutoDataFlow"
            className="h-16 md:h-28 w-auto object-contain hover:scale-105 transition-transform cursor-pointer"
            onClick={() => router.push('/')}
          />
        </div>

        {/* Full Screen Hero */}
        <section className="relative z-0 h-screen w-full">
          <HeroSection />
        </section>

        {/* Floating Magic Bar & Workspace - Overlapping Hero */}
        <div className="relative z-10 w-full bg-background -mt-0 rounded-t-[2rem] md:rounded-t-[3rem] shadow-[0_-10px_40px_rgba(0,0,0,0.5)] border-t border-white/5 pb-20">

          <div className="container mx-auto px-4 pt-10 md:pt-16 space-y-12 md:space-y-24">

            {/* 1. Magic Bar Area */}
            <div className="flex flex-col items-center space-y-6 md:space-y-8 max-w-4xl mx-auto">
              <div className="text-center space-y-4">
                <h2 className="text-3xl md:text-5xl font-bold tracking-tight bg-gradient-to-r from-white to-white/50 bg-clip-text text-transparent">
                  What do you want to find?
                </h2>
                <p className="text-muted-foreground text-lg md:text-xl max-w-2xl">
                  Scrape any website or generate synthetic datasets instantly with our AI-powered engine.
                </p>
              </div>

              <div className="w-full">
                <MagicBar
                  onSubmit={(req) => createJobMutation.mutate(req)}
                  isLoading={createJobMutation.isPending}
                />
              </div>
            </div>

            {/* 2. Workspace Sidebar (Fixed Trigger) */}
            <WorkspaceSidebar />

            {/* Features (Platform Overview) */}
            <div className="pt-8">
              <FeaturesGrid />
            </div>

            {/* 3. Landing Sections */}
            <FeaturesSection />

            <FAQSection />
            <ContactSection />

          </div>

          <Footer />
        </div>

      </main>
    </SmoothScroll>
  )
}
