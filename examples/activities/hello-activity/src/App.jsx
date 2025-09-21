import React, { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || ''

export default function App() {
    const [status, setStatus] = useState('...')
    const [component, setComponent] = useState('')
    const [error, setError] = useState('')
    const [echo, setEcho] = useState(null)

    useEffect(() => {
        const url = `${API_BASE}/activities/health`
        fetch(url)
            .then(async (r) => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`)
                const data = await r.json()
                setStatus(data.status)
                setComponent(data.component)
            })
            .catch((e) => setError(String(e)))
    }, [])

    const pingEcho = async () => {
        try {
            const url = `${API_BASE}/activities/echo?q=ping`
            const r = await fetch(url)
            if (!r.ok) throw new Error(`HTTP ${r.status}`)
            const data = await r.json()
            setEcho(data)
            setError('')
        } catch (e) {
            setError(String(e))
        }
    }

    return (
        <div style={{ fontFamily: 'sans-serif', padding: 20 }}>
            <h1>Hello Activity</h1>
            <p>API Base: <code>{API_BASE || '(same origin)'}</code></p>
            <p>Status: <strong>{status}</strong> {component && `(component: ${component})`}</p>
            {error && <p style={{ color: 'tomato' }}>Error: {error}</p>}
            <div style={{ marginTop: 16 }}>
                <button onClick={pingEcho}>Ping /activities/echo</button>
                {echo && (
                    <pre style={{ background: '#f7f7f7', padding: 12, marginTop: 8 }}>
                        {JSON.stringify(echo, null, 2)}
                    </pre>
                )}
            </div>
            <p style={{ marginTop: 24, fontSize: 12, opacity: 0.7 }}>
                Tip: set <code>VITE_API_BASE</code> to your tunneled API URL (e.g.,
                <code>https://example.trycloudflare.com</code>)
            </p>
        </div>
    )
}
