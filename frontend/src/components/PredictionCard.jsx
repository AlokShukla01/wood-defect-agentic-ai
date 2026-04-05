export default function PredictionCard({ result }) {

  const status = result.prediction.status
  const defect = result.prediction.defect_type
  const confidence = (result.confidence * 100).toFixed(2)

  return (
    <div className="glass-card rounded-[1.7rem] p-5">
      <div className="flex items-center justify-between gap-4">
        <h3 className="text-xl font-bold">Prediction</h3>
        <span className={`badge-pill ${status === "defect" ? "text-rose-200" : "text-emerald-200"}`}>
          {status === "defect" ? "Defect detected" : "Normal surface"}
        </span>
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <div className="metric-tile">
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--accent-2)]">Primary label</p>
          <p className="mt-3 text-3xl font-bold text-white">
            {status === "defect" ? defect : "Normal"}
          </p>
          {result.prediction_source && (
            <p className="mt-2 text-sm text-[var(--muted)]">
              Source: {result.prediction_source}
            </p>
          )}
        </div>

        <div className="metric-tile">
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--accent-3)]">Decision signal</p>
          <p className="mt-3 text-3xl font-bold text-white">{confidence}%</p>
          <p className="mt-2 text-sm text-[var(--muted)]">Agent action: {result.agent_action}</p>
        </div>
      </div>
    </div>
  )
}
