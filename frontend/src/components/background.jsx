import { useEffect, useState } from "react"

export default function Background() {
  const [scrollY, setScrollY] = useState(0)

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY)
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // change gradient based on scroll
  const bgStyle = {
    transform: `translateY(${scrollY * 0.04}px)`,
  }

  return (
    <div
      style={bgStyle}
      className="fixed inset-0 -z-10 overflow-hidden transition-transform duration-300"
    >
      <div
        className="absolute -left-16 top-24 h-[28rem] w-[28rem] rounded-full bg-[radial-gradient(circle,_rgba(255,209,102,0.28),_transparent_65%)] blur-2xl"
        style={{
          transform: `translateY(${scrollY * 0.1}px)`,
        }}
      />

      <div
        className="absolute right-[-6rem] top-[18rem] h-[32rem] w-[32rem] rounded-full bg-[radial-gradient(circle,_rgba(120,224,143,0.26),_transparent_65%)] blur-2xl"
        style={{
          transform: `translateY(${scrollY * -0.08}px)`,
        }}
      />

      <div className="absolute inset-x-0 top-0 h-[34rem] bg-[radial-gradient(circle_at_top,_rgba(103,213,255,0.12),_transparent_58%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(135deg,_rgba(8,22,27,0.88),_rgba(10,30,35,0.62),_rgba(11,26,28,0.92))]" />
    </div>
  )
}
