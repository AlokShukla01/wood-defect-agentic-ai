export default function MetricsCard({ metrics, result }) {

  const confidence = (result?.confidence * 100).toFixed(2)

  const iou = metrics?.iou
  const dice = metrics?.dice
  const acc = metrics?.accuracy
  const evaluationModel = result?.evaluation_model

  // -----------------------------
  // Quality Indicator (based on IoU)
  // -----------------------------
  let qualityText = "No evaluation data"
  let qualityColor = "text-gray-400"

  if (iou !== undefined && iou !== null) {
    if (iou > 0.6) {
      qualityText = "High quality prediction"
      qualityColor = "text-green-400"
    } else if (iou > 0.3) {
      qualityText = "Moderate quality"
      qualityColor = "text-yellow-400"
    } else {
      qualityText = "Low quality - needs review"
      qualityColor = "text-red-400"
    }
  }

  return (
    <div className="glass-card rounded-[1.7rem] p-5">
      <h3 className="text-xl font-bold">Model Performance</h3>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="metric-tile">
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--accent)]">Confidence</p>
          <p className="mt-2 text-2xl font-bold">{confidence}%</p>
        </div>
        <div className="metric-tile">
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--accent-3)]">Evaluation model</p>
          <p className="mt-2 text-lg font-semibold">{evaluationModel || "N/A"}</p>
        </div>
        <div className="metric-tile">
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--accent-2)]">IoU</p>
          <p className="mt-2 text-2xl font-bold">{iou !== undefined ? iou.toFixed(3) : "N/A"}</p>
        </div>
        <div className="metric-tile">
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--accent-2)]">Dice</p>
          <p className="mt-2 text-2xl font-bold">{dice !== undefined ? dice.toFixed(3) : "N/A"}</p>
        </div>
      </div>

      <div className="mt-3 metric-tile">
        <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted)]">Pixel accuracy</p>
        <p className="mt-2 text-xl font-semibold">{acc !== undefined ? acc.toFixed(3) : "N/A"}</p>
        <p className={`mt-3 text-sm ${qualityColor}`}>
          {qualityText}
        </p>
      </div>
    </div>
  )
}
