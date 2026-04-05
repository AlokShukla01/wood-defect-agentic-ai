import { motion } from "framer-motion"

export default function Hero() {
  return (
    <section className="section-shell flex min-h-screen items-center pt-28">
      <div className="grid w-full items-center gap-12 lg:grid-cols-[1.15fr_0.85fr]">
        <div>
          <motion.div
            className="section-kicker"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
          >
            Live Inspection Studio
          </motion.div>

          <motion.h1
            className="mt-6 max-w-4xl text-5xl font-bold leading-[0.96] sm:text-6xl lg:text-7xl"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
          >
            Wood defect detection with a sharper eye and an agentic review loop.
          </motion.h1>

          <motion.p
            className="mt-6 max-w-2xl text-lg leading-8 text-[var(--muted)]"
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 }}
          >
            Upload production images, inspect localized defect masks, compare against dataset ground truth,
            and let the agent decide whether to monitor, request feedback, or retrain the model.
          </motion.p>

          <motion.div
            className="mt-8 flex flex-col gap-4 sm:flex-row"
            initial={{ opacity: 0, y: 28 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.14 }}
          >
            <a href="#upload" className="wood-button px-7 py-3.5 text-base">
              Start Inspection
            </a>
            <a href="#dashboard" className="secondary-button px-7 py-3.5 text-base text-center">
              Explore Dashboard
            </a>
          </motion.div>
        </div>

        <motion.div
          className="interactive-border glass-card rounded-[2rem] p-6"
          initial={{ opacity: 0, x: 40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.12 }}
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="metric-tile">
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--accent-2)]">Pipeline</p>
              <h3 className="mt-3 text-2xl font-bold">Classifier + PaDiM + U-Net</h3>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                Multi-stage inference to classify, localize, and evaluate wood surface defects.
              </p>
            </div>
            <div className="metric-tile">
              <p className="text-xs uppercase tracking-[0.18em] text-[var(--accent)]">Agent Layer</p>
              <h3 className="mt-3 text-2xl font-bold">Review, feedback, retraining</h3>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                The system interprets uncertainty and recommends the next operational step.
              </p>
            </div>
            <div className="metric-tile sm:col-span-2">
              <div className="flex flex-wrap gap-3">
                <span className="badge-pill">Defect typing</span>
                <span className="badge-pill">Mask comparison</span>
                <span className="badge-pill">Workflow memory</span>
                <span className="badge-pill">Retraining control</span>
              </div>
              <div className="mt-5 h-44 rounded-[1.4rem] border border-white/10 bg-[linear-gradient(135deg,_rgba(255,209,102,0.12),_rgba(103,213,255,0.08),_rgba(120,224,143,0.18))] p-5">
                <div className="flex h-full flex-col justify-between">
                  <div className="flex items-center justify-between text-sm text-[var(--muted)]">
                    <span>Inspection command center</span>
                    <span>Responsive UI</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <p className="text-xs text-[var(--accent-2)]">Visual</p>
                      <p className="mt-3 text-xl font-semibold">Heatmap</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <p className="text-xs text-[var(--accent-3)]">Logic</p>
                      <p className="mt-3 text-xl font-semibold">Agent Plan</p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                      <p className="text-xs text-[var(--accent)]">Ops</p>
                      <p className="mt-3 text-xl font-semibold">Retraining</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
