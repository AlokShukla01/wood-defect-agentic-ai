export default function GroundTruthComparison({ result }) {

  if (!result?.predicted_mask || !result?.actual_ground_truth_mask) {
    return null
  }

  const predictedMaskSrc = `data:image/png;base64,${result.predicted_mask}`
  const actualMaskSrc = `data:image/png;base64,${result.actual_ground_truth_mask}`
  const comparisonOverlaySrc = result?.comparison_overlay
    ? `data:image/png;base64,${result.comparison_overlay}`
    : null
  const comparisonStats = result?.comparison_stats
  const evaluationModel = result?.evaluation_model || "N/A"

  return (
    <div className="glass-card rounded-[1.8rem] p-5 md:col-span-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-2xl font-bold">Ground Truth Comparison</h3>
        <span className="badge-pill">Evaluation Model: {evaluationModel}</span>
      </div>

      <p className="mb-5 mt-3 text-sm text-[var(--muted)]">
        Compare the evaluation mask against the dataset mask and inspect where they overlap or disagree.
      </p>

      <div className="mb-5 flex flex-wrap gap-3 text-xs">
        <span className="badge-pill text-green-200">
          Green = overlap
        </span>
        <span className="badge-pill text-orange-200">
          Orange = extra predicted area
        </span>
        <span className="badge-pill text-red-200">
          Red = missed ground truth
        </span>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div>
          <p className="mb-2 text-sm text-[var(--accent-2)]">Evaluated Mask</p>
          <img
            src={predictedMaskSrc}
            alt="Predicted evaluation mask"
            className="w-full rounded-[1.3rem] border border-white/10 bg-black/30"
          />
        </div>

        <div>
          <p className="mb-2 text-sm text-green-300">Dataset Ground Truth</p>
          <img
            src={actualMaskSrc}
            alt="Actual dataset ground truth mask"
            className="w-full rounded-[1.3rem] border border-white/10 bg-black/30"
          />
        </div>

        {comparisonOverlaySrc && (
          <div>
            <p className="mb-2 text-sm text-cyan-300">Overlap And Errors</p>
            <img
              src={comparisonOverlaySrc}
              alt="Comparison overlay between predicted and actual masks"
              className="w-full rounded-[1.3rem] border border-white/10 bg-black/30"
            />
          </div>
        )}
      </div>

      {comparisonStats && (
        <div className="mt-5 grid gap-3 text-sm md:grid-cols-3">
          <div className="metric-tile">
            <p className="text-green-300">Matched Pixels</p>
            <p className="text-white mt-1">
              {comparisonStats.true_positive_pixels}
            </p>
          </div>

          <div className="metric-tile">
            <p className="text-orange-300">Extra Predicted Pixels</p>
            <p className="text-white mt-1">
              {comparisonStats.false_positive_pixels}
            </p>
          </div>

          <div className="metric-tile">
            <p className="text-red-300">Missed GT Pixels</p>
            <p className="text-white mt-1">
              {comparisonStats.false_negative_pixels}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
