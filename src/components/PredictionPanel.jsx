import {
  Card,
  CardHeader,
  CardTitle,
  CardContent
} from "@/components/ui/card"

import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

export default function PredictionPanel({ prediction }) {

  if (!prediction) {
    return (
      <Card className="cyber-card min-h-55 bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl p-6 shadow-[0_0_20px_rgba(0,255,140,0.15)] text-gray-200">

        <CardHeader className="text-center pb-4">
          <CardTitle className="text-xl text-green-400 tracking-wide">
            Prediction
          </CardTitle>
        </CardHeader>

        <CardContent className="text-muted-foreground">
          Upload an image to see prediction results.
        </CardContent>

      </Card>
    )
  }

  const isDefect = prediction.result === "Defect"

  return (
    <Card className="cyber-card bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl p-6 shadow-[0_0_20px_rgba(0,255,140,0.15)]">

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-xl text-green-400 tracking-wide">
          Prediction Result
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-5 text-center">

        {/* Status */}
        <div className="flex items-center gap-3">

          <span>Status:</span>

          {isDefect ? (
            <Badge variant="destructive">Defect</Badge>
          ) : (
            <Badge>Normal</Badge>
          )}

        </div>

        {/* Defect Type */}
        <div>
          <p className="text-sm text-muted-foreground">
            Defect Type
          </p>

          <p className="font-medium">
            {prediction.defect_type || "None"}
          </p>
        </div>

        {/* Confidence */}
        <div>

          <p className="text-sm text-muted-foreground">
            Confidence
          </p>

          <Progress value={prediction.confidence * 100} />

          <p className="text-xs mt-1">
            {(prediction.confidence * 100).toFixed(2)}%
          </p>

        </div>

        {/* Anomaly Score */}
        <div>

          <p className="text-sm text-muted-foreground">
            Anomaly Score
          </p>

          <p className="font-medium">
            {prediction.anomaly_score}
          </p>

        </div>

        {/* Model Info */}
        <div className="text-sm text-muted-foreground">

          <p>
            Model Version: {prediction.model_version}
          </p>

          <p>
            Last Retrain: {prediction.last_retrain}
          </p>

        </div>

      </CardContent>

    </Card>
  )
}