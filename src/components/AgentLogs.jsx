import { useState, useEffect } from "react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function AgentLogs() {

  const allLogs = [
    "[INFO] Image received",
    "[INFO] Preprocessing started",
    "[INFO] Features extracted",
    "[INFO] CNN inference running",
    "[OK] Anomaly score calculated",
    "[OK] Defect classified",
    "[INFO] Checking for new defect type",
    "[OK] Model confidence verified"
  ]

  const [logs, setLogs] = useState([])

  useEffect(() => {

    let index = 0

    const interval = setInterval(() => {

      setLogs(prev => [...prev, allLogs[index]])

      index++

      if (index === allLogs.length) {
        clearInterval(interval)
      }

    }, 700)

    return () => clearInterval(interval)

  }, [])

  return (

    <Card className="cyber-card min-h-55 bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl p-6 shadow-[0_0_20px_rgba(0,255,140,0.15)] text-gray-200">

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-xl text-green-400 tracking-wide">
          Agent Decision Logs
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 text-center">

        <ul className="font-mono text-sm space-y-1">

          {logs.map((log, i) => (
            <li key={i} className="text-green-400">
              {log}
            </li>
          ))}

        </ul>

      </CardContent>

    </Card>

  )

}