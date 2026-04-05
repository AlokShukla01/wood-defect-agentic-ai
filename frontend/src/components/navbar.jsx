import { motion } from "framer-motion"

export default function Navbar() {
  return (
    <motion.div
      className="fixed inset-x-0 top-0 z-50"
      initial={{ y: -50 }}
      animate={{ y: 0 }}
    >
      <div className="section-shell mt-4">
        <div className="glass-card flex items-center justify-between rounded-full px-5 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[radial-gradient(circle,_#ffd166,_#ef9b34)] text-sm font-bold text-slate-900">
              WA
            </div>
            <div>
              <h1 className="text-lg font-bold text-[var(--text)]">
                WoodAI Inspector
              </h1>
              <p className="text-xs text-[var(--muted)]">
                Agent-assisted wood defect analysis
              </p>
            </div>
          </div>

          <div className="hidden items-center gap-3 text-sm text-[var(--muted)] md:flex">
            <a className="badge-pill hover:text-white" href="#upload">Analyze</a>
            <a className="badge-pill hover:text-white" href="#dashboard">Dashboard</a>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
