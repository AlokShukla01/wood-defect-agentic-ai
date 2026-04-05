import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import axios from "axios"
import ScanLoader from "./scanLoader"

export default function UploadBox({ setResult, setPreview, setUploadedFile }) {

  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)

  const onDrop = useCallback((acceptedFiles) => {
    const selected = acceptedFiles[0]

    if (selected) {
      setFile(selected)
      setPreview(URL.createObjectURL(selected))
      setUploadedFile(selected)
    }
  }, [setPreview, setUploadedFile])

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: { "image/*": [] },
    multiple: false,
  })

  const handleUpload = async () => {

    if (!file) {
      alert("Upload image")
      return
    }

    setLoading(true)

    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/predict",
        formData
      )

      setResult(res.data)

    } catch (err) {
      console.error(err)
      alert("Upload error")
    }

    setLoading(false)
  }

  return (
    <section id="upload" className="section-shell py-10">
      <div className="interactive-border glass-card rounded-[2rem] p-6 sm:p-8">
        <div className="grid gap-8 lg:grid-cols-[0.88fr_1.12fr] lg:items-center">
          <div>
            <span className="section-kicker">Inspection Input</span>
            <h2 className="mt-5 text-3xl font-bold sm:text-4xl">Upload a board image and launch a full agent-guided analysis.</h2>
            <p className="mt-4 max-w-xl text-[var(--muted)]">
              Drop a wood surface image to generate a defect type, anomaly score, localized mask, agent review plan,
              and retraining guidance in one responsive dashboard.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <span className="badge-pill">PNG / JPG</span>
              <span className="badge-pill">Mask evaluation</span>
              <span className="badge-pill">Feedback-ready</span>
            </div>
          </div>

          <div className="soft-card rounded-[1.6rem] p-5 text-center sm:p-6">
            <h3 className="text-xl font-semibold text-white">Upload Wood Image</h3>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Drag and drop for a faster workflow or click to browse.
            </p>

            <div
              {...getRootProps()}
              className="mt-6 rounded-[1.5rem] border border-dashed border-[var(--line-strong)] bg-black/20 p-8 transition hover:border-[var(--accent)] hover:bg-black/28 cursor-pointer"
            >
          <input {...getInputProps()} />
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[rgba(120,224,143,0.14)] text-2xl">
                ⬆
              </div>
              <p className="mt-4 text-base font-medium text-white">Drop the inspection image here</p>
              <p className="mt-2 text-sm text-[var(--muted)]">Single image input, responsive dashboard output</p>
            </div>

            {file && (
              <div className="mt-4 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-left">
                <p className="text-xs uppercase tracking-[0.18em] text-[var(--accent-2)]">Selected file</p>
                <p className="mt-2 truncate text-sm text-white">{file.name}</p>
              </div>
            )}

            <button
              onClick={handleUpload}
              className="wood-button mt-5 w-full px-6 py-3"
            >
              Analyze Image
            </button>

            <div className="mt-5 flex justify-center">
              {loading && <ScanLoader />}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
