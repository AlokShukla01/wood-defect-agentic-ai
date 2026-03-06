import { Cpu, Activity, Database } from "lucide-react"
import { useState, useEffect } from "react"

export default function StatusBar() {

    const [gpu, setGpu] = useState(70)
    const [latency, setLatency] = useState(120)
    const [fps, setFps] = useState(24)

    useEffect(() => {

        const interval = setInterval(() => {

            setGpu(65 + Math.floor(Math.random() * 15))
            setLatency(100 + Math.floor(Math.random() * 40))
            setFps(20 + Math.floor(Math.random() * 10))

        }, 1000)

        return () => clearInterval(interval)

    }, [])

    const stats = [
        { icon: Cpu, label: "Model", value: "Active" },
        { icon: Activity, label: "Latency", value: latency + " ms" },
        { icon: Database, label: "GPU", value: gpu + "%" },
        { icon: Activity, label: "FPS", value: fps }
    ]

    return (

        <div className="status-bar cyber-card bg-black/30 backdrop-blur-md border border-green-400/20 rounded-lg px-5 py-2 max-w-xl mx-auto shadow-[0_0_12px_rgba(0,255,140,0.15)] ">

            <div className="flex justify-center gap-8 text-xs font-mono text-gray-300">

                {stats.map((s, i) => {

                    const Icon = s.icon

                    return (

                        <div key={i} className="flex items-center gap-2">

                            <Icon size={16} className="text-green-400" />

                            <span className="text-gray-400">{s.label}:</span>

                            <span className="text-green-400">{s.value}</span>

                        </div>

                    )

                })}

            </div>

        </div>

    )

}