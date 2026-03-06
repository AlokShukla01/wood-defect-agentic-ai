import { useEffect, useRef } from "react"

export default function MatrixRain() {

  const canvasRef = useRef(null)

  useEffect(() => {

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")

    const letters =
      "アイウエオカキクケコサシスセソタチツテト0123456789"

    const fontSize = 18
    let mouseX = 0
    let mouseY = 0
    

    let columns
    let drops

    function resize() {

      canvas.width = window.innerWidth
      canvas.height = window.innerHeight

      columns = Math.floor(canvas.width / fontSize)
      drops = Array(columns).fill(1)

    }

    resize()
    window.addEventListener("resize", resize)

    window.addEventListener("mousemove", (e) => {
      mouseX = e.clientX
      mouseY = e.clientY
    })

    function draw() {

      // clear screen properly
      ctx.fillStyle = "rgba(0,0,0,0.18)"
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      ctx.fillStyle = "#00ff9c"
      ctx.shadowColor = "#00ff9c"
      ctx.shadowBlur = 8
      ctx.font = fontSize + "px monospace"

      for (let i = 0; i < drops.length; i++) {

        const text =
          letters[Math.floor(Math.random() * letters.length)]

        let x = i * fontSize
        let y = drops[i] * fontSize

        const dx = x - mouseX
        const dy = y - mouseY
        const dist = Math.sqrt(dx * dx + dy * dy)

        const radius = 180

        if (dist < radius) {
          const force = (radius - dist) / radius
          x += dx * force * 0.4
          y += dy * force * 0.2
        }

        ctx.fillText(text, x, y)

        if (y > canvas.height && Math.random() > 0.975) {
          drops[i] = 0
        }

        drops[i]++

      }

    }

    const interval = setInterval(draw, 40)

    return () => {

      clearInterval(interval)
      window.removeEventListener("resize", resize)

    }

  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        zIndex: -1,
        background: "black"
      }}
    />
  )

}