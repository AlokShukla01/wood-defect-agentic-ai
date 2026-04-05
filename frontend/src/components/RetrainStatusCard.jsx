import { useEffect, useRef, useState } from "react"

export default function RetrainStatusCard() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState("")
  const previousStateRef = useRef(null)

  useEffect(() => {
    let ignore = false
    let intervalId = null

    async function loadStatus() {
      try {
        const response = await fetch("http://127.0.0.1:8000/retrain/status")
        const payload = await response.json()

        if (!response.ok) {
          throw new Error(payload.detail || "Failed to load retraining status")
        }

        if (!ignore) {
          const previousState = previousStateRef.current
          previousStateRef.current = payload.state
          setStatus(payload)
          setError("")

          if (
            previousState === "running" &&
            payload.state !== "running"
          ) {
            window.dispatchEvent(new CustomEvent("retraining-completed"))
            window.dispatchEvent(new CustomEvent("agent-review-updated"))
          }

          if (payload.state === "running" && intervalId === null) {
            intervalId = setInterval(loadStatus, 2000)
          } else if (payload.state !== "running" && intervalId !== null) {
            clearInterval(intervalId)
            intervalId = null
          }
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message || "Failed to load retraining status")
        }
      }
    }

    function handleRetrainingStarted() {
      loadStatus()

      if (intervalId === null) {
        intervalId = setInterval(loadStatus, 2000)
      }
    }

    loadStatus()
    window.addEventListener("retraining-started", handleRetrainingStarted)

    return () => {
      ignore = true
      window.removeEventListener("retraining-started", handleRetrainingStarted)
      if (intervalId !== null) {
        clearInterval(intervalId)
      }
    }
  }, [])

  async function handleRefresh() {
    try {
      const response = await fetch("http://127.0.0.1:8000/retrain/status")
      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.detail || "Failed to load retraining status")
      }

      setStatus(payload)
      setError("")
    } catch (err) {
      setError(err.message || "Failed to load retraining status")
    }
  }

  const progress = status?.progress ?? 0
  const isRunning = status?.state === "running"

  return (
    <div className="glass-card rounded-[1.8rem] p-5 md:col-span-2">
      <h3 className="text-2xl font-bold">Retraining Status</h3>

      <div className="mt-3 flex flex-wrap gap-3">
        <button
          onClick={handleRefresh}
          className="rounded-full border border-white/12 bg-black/18 px-4 py-2 text-sm text-white transition hover:bg-black/28"
        >
          Refresh Status
        </button>
      </div>

      {error && (
        <p className="mt-3 text-sm text-red-300">{error}</p>
      )}

      {!error && status && (
        <>
          <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
            <span className="badge-pill text-cyan-200">
              State: {status.state}
            </span>
            <span className="badge-pill">
              Progress: {progress}%
            </span>
            <span className="badge-pill">
              Epoch: {status.current_epoch}/{status.total_epochs || 0}
            </span>
          </div>

          <div className="mt-5 h-3 overflow-hidden rounded-full bg-white/10">
            <div
              className={`h-full rounded-full transition-all ${isRunning ? "bg-cyan-400" : "bg-green-400"}`}
              style={{ width: `${progress}%` }}
            />
          </div>

          <p className="mt-4 text-sm text-[var(--muted)]">
            {status.message}
          </p>

          {status.last_error && (
            <p className="mt-3 text-sm text-red-300">
              {status.last_error}
            </p>
          )}
        </>
      )}
    </div>
  )
}
