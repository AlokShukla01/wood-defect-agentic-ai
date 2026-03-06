import Dashboard from "./pages/Dashboard"
import MatrixRain from "@/components/ui/matrix"

function App() {

  return (
    <div className="min-h-screen">

      <MatrixRain />

      <div className=" pointer-events-none fixed inset-0 z-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0.85)_0%,rgba(0,0,0,0.55)_40%,transparent_70%)] "></div>

      <div className="relative z-10">
        <Dashboard />
      </div>

    </div>
  )
}

export default App