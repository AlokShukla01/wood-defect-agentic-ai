import Navbar from "./components/navbar"
import Hero from "./components/hero"
import UploadBox from "./components/uploadBox"
import Footer from "./components/footer"
import Dashboard from "./components/Dashboard"
import { useState } from "react"

export default function Home() {
  const [result, setResult] = useState(null)
  const [preview, setPreview] = useState(null)
  const [uploadedFile, setUploadedFile] = useState(null)

  return (
    <div className="app-shell relative z-10 text-white">
      <div className="grain-overlay" />
      <Navbar />
      <Hero />

      <UploadBox
        setResult={setResult}
        setPreview={setPreview}
        setUploadedFile={setUploadedFile}
      />

      {result && (
        <Dashboard result={result} preview={preview} uploadedFile={uploadedFile} />
      )}

      <Footer />
    </div>
  )
}
