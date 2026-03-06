import { Card, CardContent } from "@/components/ui/card"
import { useDropzone } from "react-dropzone"
import axios from "axios"
import { UploadCloud } from "lucide-react"

export default function UploadZone({ setImage, setPrediction }) {

  const onDrop = async (acceptedFiles) => {

    const file = acceptedFiles[0]

    setImage(URL.createObjectURL(file))

    const formData = new FormData()
    formData.append("image", file)

    try {

      const res = await axios.post(
        "http://localhost:8000/predict",
        formData
      )

      setPrediction(res.data)

    } catch (err) {

      console.error(err)

    }

  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop })

  return (
    <Card className="cyber-card bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl shadow-[0_0_20px_rgba(0,255,140,0.15)]  ">

      <CardContent
        {...getRootProps()}
        className={`p-10 space-y-4 border-2 border-dashed rounded-xl text-center transition-all duration-300 cursor-pointer bg-black/40 backdrop-blur-xl ${isDragActive ? "border-green-300 shadow-[0_0_30px_rgba(0,255,140,0.5)] scale-[1.02]" : "border-green-400/40 hover:border-green-300 hover:shadow-[0_0_25px_rgba(0,255,140,0.3)]"}`}
      >

        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-3">

          <UploadCloud
            size={56}
            className={`transition-all duration-300 ${isDragActive ? "text-green-300 scale-110" : "text-green-400"
              }`}
          />

          <p className="text-lg font-semibold text-gray-200 transition-all">

            {isDragActive
              ? "Drop Image To Analyze ⚡"
              : "Drag & Drop Product Image"}

          </p>

          <p className="text-sm text-gray-400">
            or click to upload
          </p>

        </div>

      </CardContent>

    </Card>
  )
}