export default function LogsCard({ logs }) {
  return (
    <div className="glass-card rounded-[1.7rem] p-5">
      <h3 className="text-xl font-bold">Agent Logs</h3>

      {logs && logs.length > 0 ? (
        <ul className="mt-4 space-y-2 text-sm text-[var(--muted)]">
          {logs.map((log, i) => (
            <li key={i} className="rounded-2xl border border-white/8 bg-black/18 px-4 py-3">
              {log}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-sm text-[var(--muted)]">
          No logs available
        </p>
      )}
    </div>
  )
}
