import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell
} from "@/components/ui/table"

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function HistoryTable() {

  const history = [
    { id: 1, result: "Normal", score: 0.12 },
    { id: 2, result: "Defect", score: 0.87 }
  ]

  return (

    <Card className="cyber-card bg-black/40 backdrop-blur-xl border border-green-400/20 rounded-xl p-6 shadow-[0_0_20px_rgba(0,255,140,0.15)] text-gray-200">

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-xl text-green-400 tracking-wide">
          Prediction History
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4 text-center">

        <Table>

          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Result</TableHead>
              <TableHead>Anomaly Score</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>

            {history.map(item => (
              <TableRow key={item.id}>
                <TableCell>{item.id}</TableCell>
                <TableCell>{item.result}</TableCell>
                <TableCell>{item.score}</TableCell>
              </TableRow>
            ))}

          </TableBody>

        </Table>

      </CardContent>

    </Card>

  )
}