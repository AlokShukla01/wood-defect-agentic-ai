import { useState, useRef } from "react"
import ReactCrop from "react-image-crop"
import "react-image-crop/dist/ReactCrop.css"

export default function ImageCard({ result, preview, uploadedFile }) {

  const heatmapImage = result?.heatmap
    ? `data:image/png;base64,${result.heatmap}`
    : null

  const imageSrc = heatmapImage || preview

  const [crop, setCrop] = useState()
  const [selectedLabel, setSelectedLabel] = useState("")

  const imgRef = useRef(null)

  // -----------------------------
  // Send Region + Label to Backend
  // -----------------------------
  const handleSubmit = async () => {

    if (!crop || !selectedLabel) {
      alert("Select region and label")
      return
    }

    try {
      if (!uploadedFile) {
        alert("Original uploaded image is missing")
        return
      }

      const formData = new FormData()
      formData.append("file", uploadedFile)
      formData.append("label", selectedLabel)
      formData.append("bbox", JSON.stringify(crop))
      formData.append("timestamp", new Date().toISOString())

      const response = await fetch("http://127.0.0.1:8000/feedback", {
        method: "POST",
        body: formData
      })

      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.detail || "Feedback request failed")
      }

      alert(payload.message || "✅ Region + label stored!")

      window.dispatchEvent(new CustomEvent("agent-review-updated"))

      // reset after submit
      setCrop(null)
      setSelectedLabel("")

    } catch (err) {
      console.error(err)
      alert("❌ Error sending data")
    }
  }

  return (
    <div className="glass-card rounded-[1.7rem] p-5">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h3 className="text-xl font-bold">Image Analysis</h3>
        <span className="badge-pill">Annotation ready</span>
      </div>

      <ReactCrop crop={crop} onChange={(_, percentCrop) => setCrop(percentCrop)}>
        <img
          ref={imgRef}
          src={imageSrc}
          className="max-h-[28rem] w-full rounded-[1.35rem] border border-white/10 bg-black/30 object-cover"
        />
      </ReactCrop>

      <p className="mt-3 text-sm text-[var(--muted)]">
        Draw box around defect region
      </p>

      <select
        className="mt-4 w-full rounded-2xl border border-white/10 bg-black/25 px-4 py-3 text-white outline-none"
        value={selectedLabel}
        onChange={(e) => setSelectedLabel(e.target.value)}
      >
        <option value="">Select defect type</option>
        <option value="color">color</option>
        <option value="combined">combined</option>
        <option value="hole">hole</option>
        <option value="liquid">liquid</option>
        <option value="scratch">scratch</option>
      </select>

      <button
        onClick={handleSubmit}
        className="wood-button mt-4 w-full px-4 py-3"
      >
        Submit Annotation
      </button>

      <p className="mt-3 text-sm text-[var(--muted)]">
        {heatmapImage
          ? "🔥 AI suggestion shown, refine with your annotation"
          : "Original image"}
      </p>
    </div>
  )
}
