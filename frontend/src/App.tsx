import { useEffect, useState } from 'react'
import './App.css'

type HealthResponse = {
  status: string
  environment: string
}

function App() {
  const [message, setMessage] = useState('Loading...')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/hello').then((res) => res.json()),
      fetch('/api/health').then((res) => res.json()),
    ])
      .then(([helloData, healthData]) => {
        setMessage(helloData.message)
        setHealth(healthData)
      })
      .catch(() => setError('Could not reach the backend API.'))
  }, [])

  return (
    <main style={{ fontFamily: 'sans-serif', maxWidth: 640, margin: '4rem auto', padding: '0 1rem' }}>
      <h1>FastAPI + React on EC2</h1>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {!error && (
        <>
          <p>{message}</p>
          {health && (
            <p>
              Backend status: <strong>{health.status}</strong> ({health.environment})
            </p>
          )}
        </>
      )}
    </main>
  )
}

export default App
