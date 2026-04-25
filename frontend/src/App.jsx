import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import MarketResearch from './pages/MarketResearch'
import Prospects from './pages/Prospects'
import Pitches from './pages/Pitches'
import Analytics from './pages/Analytics'
import FollowUps from './pages/FollowUps'

export default function App() {
  const profileId = localStorage.getItem('profileId')

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/setup" element={<Onboarding />} />
        <Route element={<Layout />}>
          <Route path="/" element={profileId ? <Dashboard /> : <Navigate to="/setup" />} />
          <Route path="/research" element={profileId ? <MarketResearch /> : <Navigate to="/setup" />} />
          <Route path="/prospects" element={profileId ? <Prospects /> : <Navigate to="/setup" />} />
          <Route path="/pitches" element={profileId ? <Pitches /> : <Navigate to="/setup" />} />
          <Route path="/analytics" element={profileId ? <Analytics /> : <Navigate to="/setup" />} />
          <Route path="/followups" element={profileId ? <FollowUps /> : <Navigate to="/setup" />} />
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}
