import { Routes, Route } from 'react-router-dom'
import { Dashboard } from './components/Dashboard'
import './index.css'

function App() {
  return (
    <div className="min-h-screen bg-slate-950">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/symbol/:symbol" element={<Dashboard />} />
      </Routes>
    </div>
  )
}

export default App
