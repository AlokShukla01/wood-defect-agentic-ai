import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { useState, useEffect } from "react"
export default function ImageViewer({ image, prediction }) {
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    if (image && !prediction) {
      setScanning(true)

      const timer = setTimeout(() => {
        setScanning(false)
      }, 2000)

      return () => clearTimeout(timer)
    }
  }, [image, prediction])
  return (
    <Card className="cyber-card bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl p-6 shadow-[0_0_20px_rgba(0,255,140,0.15)] text-gray-200">

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-xl text-green-400 tracking-wide">
          Image Analysis
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 text-center">

        {!image && (
          <div className="cyber-card min-h-55 bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl p-6 shadow-[0_0_20px_rgba(0,255,140,0.15)]">
            No image uploaded
          </div>
        )}

        {image && (
          <div className="relative">

            {/* Original Image */}
            <img
              src={image}
              alt="uploaded"
              className="rounded-lg w-full"
            />
            <div className="inspection-overlay"></div>
            {scanning && (
              <div className="scan-line"></div>
            )}

            {/* Heatmap Overlay */}
            {prediction?.heatmap && (
              <img
                src={prediction.heatmap}
                className="absolute top-0 left-0 opacity-60 w-full"
              />
            )}

            {prediction?.result === "Defect" && (
              <div className="defect-box">
                DEFECT
              </div>
            )}

            {/* Mask Overlay */}
            {prediction?.mask && (
              <img
                src={prediction.mask}
                className="absolute top-0 left-0 opacity-50 w-full"
              />
            )}

          </div>
        )}

      </CardContent>

    </Card>
  )
}