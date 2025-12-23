"use client"

import { useEffect } from "react"

export function SmoothScroll({ children }: { children: React.ReactNode }) {
    useEffect(() => {
        (async () => {
            try {
                // @ts-expect-error locomotive-scroll lacks types
                const LocomotiveScroll = (await import("locomotive-scroll")).default

                // Initialize
                new LocomotiveScroll({
                    lenisOptions: {
                        wrapper: window,
                        content: document.documentElement,
                        lerp: 0.1,
                        duration: 1.2,
                        orientation: 'vertical',
                        gestureOrientation: 'vertical',
                        smoothWheel: true,
                        wheelMultiplier: 1,
                        touchMultiplier: 2,
                    }
                })
            } catch (e) {
                console.error("Locomotive Scroll failed to load:", e)
            }
        })()
    }, [])

    return (
        <div className="w-full min-h-screen">
            {children}
        </div>
    )
}
