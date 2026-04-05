import { motion } from "framer-motion"

export default function ScanLoader() {
  return (
    <div className="relative h-52 w-full max-w-sm overflow-hidden rounded-[1.5rem] border border-[var(--line-strong)] bg-black/25">
      
      <motion.div
        className="absolute left-0 h-14 w-full bg-[linear-gradient(180deg,_rgba(120,224,143,0.26),_transparent)]"
        animate={{ top: ["0%", "100%", "0%"] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      />

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(103,213,255,0.06),_transparent_60%)]" />

      <div className="relative flex h-full flex-col items-center justify-center gap-2">
        <div className="h-16 w-16 rounded-full border border-[var(--line-strong)] bg-white/5" />
        <p className="text-lg font-semibold text-white">Scanning surface map</p>
        <p className="text-sm text-[var(--muted)]">Running defect classification and anomaly review...</p>
      </div>
    </div>
  )
}
