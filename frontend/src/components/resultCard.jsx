import { motion } from "framer-motion"

export default function ResultCard({ result }) {
  return (
    <motion.div
      className="mt-10 bg-white/10 backdrop-blur-lg p-6 rounded-xl w-80"
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h2 className="text-xl font-semibold">Result</h2>

      <p className="mt-2 text-green-400 text-lg">
        {result.class}
      </p>

      <p className="text-gray-400">
        Confidence: {(result.confidence * 100).toFixed(2)}%
      </p>
    </motion.div>
  )
}