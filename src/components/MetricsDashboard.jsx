import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts"

export default function MetricsDashboard() {

  const data = [
    { name: "Accuracy", value: 0.94 },
    { name: "Precision", value: 0.92 },
    { name: "Recall", value: 0.90 },
    { name: "IoU", value: 0.87 }
  ]

  return (
    <Card className="cyber-card min-h-55 bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl p-6 shadow-[0_0_20px_rgba(0,255,140,0.15)] text-gray-200">

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-xl text-green-400 tracking-wide">
          Model Performance
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 text-center">

        <BarChart width={350} height={200} data={data}>
          <XAxis
            dataKey="name"
            stroke="#9ca3af"
            tick={{ fill: "#9ca3af" }}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: "#9ca3af" }}
          />
          <Tooltip
            contentStyle={{
              background: "#021a12",
              border: "1px solid #00ff9c",
              color: "#00ff9c"
            }}
          />
          <Bar
            dataKey="value"
            fill="#00ff9c"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>

      </CardContent>

    </Card>
  )
}