import ImageCard from "./ImageCard"
import AgentReviewCard from "./AgentReviewCard"
import PredictionCard from "./PredictionCard"
import LogsCard from "./LogsCard"
import MetricsCard from "./MetricsCard"
import GroundTruthComparison from "./GroundTruthComparison"
import RetrainStatusCard from "./RetrainStatusCard"

export default function Dashboard({ result, preview, uploadedFile }) {
  const agent = result.agent
  const reasoning = agent?.reasoning || []
  const nextSteps = agent?.next_steps || []
  const rulePlan = agent?.rule_based_plan || agent
  const workflowManager = agent?.workflow_manager
  const reviewRefreshKey = JSON.stringify({
    anomalyScore: result.anomaly_score,
    defectType: result.prediction?.defect_type,
    status: result.prediction?.status,
    confidence: result.confidence,
    agentAction: result.agent_action,
  })

  // -----------------------------
  // Generate Logs (Agent style)
  // -----------------------------
  const logs = [
    "Image received",
    "Preprocessing completed",
    "Feature extraction done",
    result.prediction.status === "normal"
      ? "No anomaly detected"
      : "Anomaly detected",
    result.prediction.status === "defect"
      ? `Classified as ${result.prediction.defect_type}`
      : "Marked as normal",
    result.requires_user_input
      ? "Low-confidence prediction routed for user review"
      : "Prediction confidence acceptable",
    `Agent decision: ${result.agent_action}`
  ].concat(reasoning)

  // -----------------------------
  // Generate Metrics
  // -----------------------------
  return (
    <section id="dashboard" className="section-shell py-12">
      <div className="mb-8 grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <div className="glass-card rounded-[2rem] p-7">
          <span className="section-kicker">Analysis Dashboard</span>
          <h2 className="mt-5 text-3xl font-bold sm:text-4xl">
            Review predictions, agent reasoning, and retraining signals in one responsive workspace.
          </h2>
          <p className="mt-4 max-w-2xl text-[var(--muted)]">
            This dashboard combines visual evidence, quality metrics, ground-truth comparison,
            and agent-driven actions so you can decide whether to accept, review, or improve the model.
          </p>
        </div>

        <div className="soft-card rounded-[2rem] p-7">
          <p className="text-xs uppercase tracking-[0.18em] text-[var(--accent-2)]">Live Snapshot</p>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="metric-tile">
              <p className="text-xs text-[var(--muted)]">Detected status</p>
              <p className="mt-2 text-xl font-semibold">{result.prediction.status}</p>
            </div>
            <div className="metric-tile">
              <p className="text-xs text-[var(--muted)]">Displayed confidence</p>
              <p className="mt-2 text-xl font-semibold">{(result.confidence * 100).toFixed(1)}%</p>
            </div>
          </div>
        </div>
      </div>

      {result.agent_action === "request_user_label" && (
        <div className="mb-6 rounded-[1.7rem] border border-[rgba(255,209,102,0.28)] bg-[rgba(255,209,102,0.08)] px-6 py-5 text-center shadow-[0_18px_45px_rgba(0,0,0,0.18)]">
          <p className="text-lg font-semibold text-[var(--accent-2)]">
            AI is unsure about this image
          </p>

          <p className="mt-2 text-[var(--muted)]">
            {result.user_message || "Please mark the defect region in the image below and select the correct label."}
          </p>
        </div>
      )}

      {agent && (
        <div className="interactive-border glass-card mb-6 rounded-[1.8rem] p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-2xl font-bold text-white">Agent Plan</h3>
              <p className="mt-3 max-w-3xl text-[var(--muted)]">
            {agent.summary}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="badge-pill">Mode: {agent.mode}</span>
              <span className="badge-pill">Confidence: {agent.confidence_level}</span>
              <span className="badge-pill">Quality: {agent.quality_level}</span>
              <span className="badge-pill">Workflow: {agent.review_source || "local_workflow"}</span>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div className="metric-tile">
              <p className="text-sm uppercase tracking-[0.18em] text-[var(--accent-2)]">Rule-Based Plan</p>
              <p className="mt-3 text-lg font-semibold text-white">{rulePlan?.summary}</p>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Action: {rulePlan?.action} | Confidence: {rulePlan?.confidence_level} | Quality: {rulePlan?.quality_level}
              </p>
              {rulePlan?.next_steps?.length > 0 && (
                <ul className="mt-3 space-y-2 text-sm text-[var(--muted)]">
                  {rulePlan.next_steps.map((step) => (
                    <li key={step} className="rounded-2xl border border-white/8 bg-black/18 px-4 py-3">{step}</li>
                  ))}
                </ul>
              )}
            </div>

            <div className="metric-tile">
              <p className="text-sm uppercase tracking-[0.18em] text-[var(--accent-3)]">Workflow Controller</p>
              <p className="mt-3 text-lg font-semibold text-white">
                {workflowManager?.available ? workflowManager.summary : "Workflow controller not active"}
              </p>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Status: {workflowManager?.status || "active"}{workflowManager?.queue_name ? ` | Queue: ${workflowManager.queue_name}` : ""}{workflowManager?.task_priority ? ` | Priority: ${workflowManager.task_priority}` : ""}
              </p>
              {workflowManager?.reasoning?.length > 0 && (
                <ul className="mt-3 space-y-2 text-sm text-[var(--muted)]">
                  {workflowManager.reasoning.map((item) => (
                    <li key={item} className="rounded-2xl border border-white/8 bg-black/18 px-4 py-3">{item}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {nextSteps.length > 0 && (
            <div className="mt-5">
              <p className="text-sm uppercase tracking-[0.18em] text-[var(--accent-3)]">Next steps</p>
              <ul className="mt-3 space-y-2 text-sm text-[var(--muted)]">
                {nextSteps.map((step) => (
                  <li key={step} className="rounded-2xl border border-white/8 bg-black/18 px-4 py-3">{step}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">

        <ImageCard preview={preview} result={result} uploadedFile={uploadedFile} />

        <PredictionCard result={result} />

        <LogsCard logs={logs} />

        <MetricsCard metrics={result.metrics} result={result} />

        <GroundTruthComparison result={result} />

        <AgentReviewCard refreshKey={reviewRefreshKey} />

        <RetrainStatusCard />

      </div>
    </section>
  )
}
