export default function History({ history }) {
    return (
      <div id="history" className="mt-20 px-6">
        <h2 className="text-2xl mb-4">Previous Scans</h2>
  
        <div className="grid grid-cols-2 gap-4">
          {history.map((item, i) => (
            <div key={i} className="bg-gray-800 p-4 rounded-lg">
              <p>{item.class}</p>
              <p className="text-gray-400 text-sm">
                {(item.confidence * 100).toFixed(1)}%
              </p>
            </div>
          ))}
        </div>
      </div>
    )
  }