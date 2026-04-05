import { useEffect, useState } from "react"

export default function AgentReviewCard({ refreshKey }) {
  const [review, setReview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [startingRetrain, setStartingRetrain] = useState(false)
  const [isRetraining, setIsRetraining] = useState(false)

  async function loadReview(triggerRetraining = false) {
    try {
      if (!review) {
        setLoading(true)
      }
      setError("")

      const query = triggerRetraining
        ? "http://127.0.0.1:8000/agent/review?limit=100&trigger_retraining=true"
        : "http://127.0.0.1:8000/agent/review?limit=100"

      const response = await fetch(query)
      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.detail || "Failed to load agent review")
      }

      setReview(payload)
      setIsRetraining(Boolean(payload.retraining_started))

      if (payload.retraining_started) {
        window.dispatchEvent(new CustomEvent("retraining-started"))
      }
    } catch (err) {
      setError(err.message || "Failed to load agent review")
    } finally {
      setLoading(false)
      setStartingRetrain(false)
    }
  }

  useEffect(() => {
    loadReview()
  }, [refreshKey])

  useEffect(() => {
    function handleReviewUpdate() {
      loadReview()
    }

    window.addEventListener("agent-review-updated", handleReviewUpdate)
    window.addEventListener("retraining-completed", handleReviewUpdate)
    window.addEventListener("focus", handleReviewUpdate)

    function handleVisibilityChange() {
      if (!document.hidden) {
        loadReview()
      }
    }

    document.addEventListener("visibilitychange", handleVisibilityChange)

    return () => {
      window.removeEventListener("agent-review-updated", handleReviewUpdate)
      window.removeEventListener("retraining-completed", handleReviewUpdate)
      window.removeEventListener("focus", handleReviewUpdate)
      document.removeEventListener("visibilitychange", handleVisibilityChange)
    }
  }, [])

  useEffect(() => {
    let intervalId = null

    async function pollStatusAndRefreshReview() {
      try {
        const response = await fetch("http://127.0.0.1:8000/retrain/status")
        const payload = await response.json()

        if (!response.ok) {
          throw new Error(payload.detail || "Failed to load retraining status")
        }

        const running = payload.state === "running"
        setIsRetraining(running)

        if (!running && intervalId !== null) {
          clearInterval(intervalId)
          intervalId = null
          await loadReview()
        }
      } catch (_) {
        // Keep the review card resilient even if status polling fails.
      }
    }

    if (startingRetrain || isRetraining) {
      intervalId = setInterval(pollStatusAndRefreshReview, 2000)
      pollStatusAndRefreshReview()
    }

    return () => {
      if (intervalId !== null) {
        clearInterval(intervalId)
      }
    }
  }, [startingRetrain, isRetraining])

  async function handleStartRetraining() {
    setStartingRetrain(true)
    await loadReview(true)
  }

  return (
    <div className="glass-card rounded-[1.8rem] p-5 md:col-span-2">
      <h3 className="text-2xl font-bold">Agent Review Loop</h3>

      <div className="mt-3 flex flex-wrap gap-3">
        <button
          onClick={() => loadReview()}
          className="rounded-full border border-white/12 bg-black/18 px-4 py-2 text-sm text-white transition hover:bg-black/28"
        >
          Refresh Review
        </button>
      </div>

      {loading && (
        <p className="mt-3 text-sm text-[var(--muted)]">
          Reviewing recent prediction and feedback logs...
        </p>
      )}

      {!loading && error && (
        <p className="mt-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {!loading && !error && review && (
        <>
          <p className="mt-3 text-lg text-cyan-200">
            Recommendation: {review.recommendation}
          </p>

          <div className="mt-5 grid gap-3 text-sm md:grid-cols-4">
            <div className="metric-tile">
              <p className="text-cyan-200">Predictions reviewed</p>
              <p className="mt-1 text-white">{review.summary.total_predictions}</p>
            </div>
            <div className="metric-tile">
              <p className="text-yellow-200">New feedback samples</p>
              <p className="mt-1 text-white">{review.summary.new_feedback_since_last_retrain}</p>
            </div>
            <div className="metric-tile">
              <p className="text-orange-200">Low-confidence rate</p>
              <p className="mt-1 text-white">
                {(review.summary.low_confidence_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div className="metric-tile">
              <p className="text-red-200">Weak mask rate</p>
              <p className="mt-1 text-white">
                {(review.summary.weak_quality_rate * 100).toFixed(1)}%
              </p>
            </div>
          </div>

          {review.reasons?.length > 0 && (
            <div className="mt-5">
              <p className="text-sm uppercase tracking-[0.18em] text-[var(--accent-3)]">Why the agent chose this</p>
              <ul className="mt-3 space-y-2 text-sm text-[var(--muted)]">
                {review.reasons.map((reason) => (
                  <li key={reason} className="rounded-2xl border border-white/8 bg-black/18 px-4 py-3">{reason}</li>
                ))}
              </ul>
            </div>
          )}

          {review.next_steps?.length > 0 && (
            <div className="mt-5">
              <p className="text-sm uppercase tracking-[0.18em] text-[var(--accent)]">Suggested next steps</p>
              <ul className="mt-3 space-y-2 text-sm text-[var(--muted)]">
                {review.next_steps.map((step) => (
                  <li key={step} className="rounded-2xl border border-white/8 bg-black/18 px-4 py-3">{step}</li>
                ))}
              </ul>
            </div>
          )}

          {review.recommendation === "start_retraining" && (
            <div className="mt-5">
              <button
                onClick={handleStartRetraining}
                disabled={startingRetrain}
                className="wood-button px-5 py-3 text-sm disabled:cursor-not-allowed disabled:opacity-60"
              >
                {startingRetrain ? "Starting Retraining..." : "Start Retraining"}
              </button>
            </div>
          )}

          {review.retraining_message && (
            <p className="mt-4 text-sm text-green-200">
              {review.retraining_message}
            </p>
          )}
        </>
      )}
    </div>
  )
}
