import Particles from "react-tsparticles"
import { loadSlim } from "tsparticles-slim"
import { useCallback } from "react"

export default function ParticlesBackground() {

  const particlesInit = useCallback(async (engine) => {
    await loadSlim(engine)
  }, [])

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 1
      }}
      options={{
        background: {
          color: {
            value: "transparent"
          }
        },

        particles: {

          number: {
            value: 400
          },
        
          color: {
            value: ["#ff9ccf", "#d6b3ff", "#ffd9a8"]
          },
        
          shape: {
            type: "circle"
          },
        
          opacity: {
            value: 1
          },
        
          size: {
            value: { min: 2, max: 5 }
          },
        
          move: {
            enable: true,
            speed: 0.6,
            direction: "none",
            outModes: {
              default: "out"
            }
          }
        },

        interactivity: {
          events: {
            onHover: {
              enable: true,
              mode: "repulse"
            }
          },
          modes: {
            repulse: {
              distance: 120
            }
          }
        }
      }}
    />
  )
}