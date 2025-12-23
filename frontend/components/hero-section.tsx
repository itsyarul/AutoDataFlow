"use client"

export function HeroSection() {
    return (
        <section className="relative w-full h-[100vh] bg-black overflow-hidden">
            <iframe
                src="https://my.spline.design/claritystream-aCG41Etj9Unw0MMAPTHyYr8h/"
                frameBorder="0"
                width="100%"
                height="100%"
                className="w-full h-full pointer-events-none"
                title="Spline 3D Scene"
            />
            {/* Overlay to ensure text visibility if needed, or just let it shine */}
            <div className="absolute inset-0 bg-black/20 pointer-events-none" />

            {/* Hide Spline Watermark */}
            <div className="absolute bottom-0 right-0 w-48 h-20 bg-black z-50 pointer-events-none" />
        </section>
    )
}
