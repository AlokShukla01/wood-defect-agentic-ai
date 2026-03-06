import { useState } from "react"
import StatusBar from "@/components/StatusBar"
import UploadZone from "@/components/UploadZone"
import ImageViewer from "@/components/ImageViewer"
import PredictionPanel from "@/components/PredictionPanel"
import AgentLogs from "@/components/AgentLogs"
import MetricsDashboard from "@/components/MetricsDashboard"
import HistoryTable from "@/components/HistoryTable"

export default function Dashboard() {

  const [image, setImage] = useState(null)
  const [prediction, setPrediction] = useState(null)

  return (
    <div className="min-h-screen text-foreground p-10 backdrop-blur-sm">

      <div className="max-w-7xl mx-auto space-y-10">

        {/* Title */}
        <h1 className="text-6xl font-bold text-green-400 text-center tracking-widest drop-shadow-[0_0_20px_#00ff9c] mb-4">
          AI Defect Detection System
        </h1>

        <StatusBar />

        {/* Upload */}
        <div className="max-w-3xl mx-auto">
          <UploadZone
            setImage={setImage}
            setPrediction={setPrediction}
          />
        </div>

        {/* Image + Prediction */}
        <div className="grid lg:grid-cols-2 gap-10 items-stretch">

          <ImageViewer
            image={image}
            prediction={prediction}
          />

          <PredictionPanel
            prediction={prediction}
          />

        </div>

        {/* Logs + Metrics */}
        <div className="grid lg:grid-cols-2 gap-8">

          <AgentLogs />

          <MetricsDashboard />

        </div>

        {/* History */}
        <HistoryTable />

      </div>

    </div>
  )
}