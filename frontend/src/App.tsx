import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './pages/Login';
import DashboardLayout from './layouts/DashboardLayout';
import Overview from './pages/Overview';
import Onboarding from './pages/Onboarding';
import SprintBoard from './pages/SprintBoard';
import Messages from './pages/Messages';
import StandupMeeting from './pages/StandupMeeting';
import Retrospective from './pages/Retrospective';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<DashboardLayout />}>
            <Route index element={<Overview />} />
            <Route path="onboarding" element={<Onboarding />} />
            <Route path="sprint" element={<SprintBoard />} />
            <Route path="standup" element={<StandupMeeting />} />
            <Route path="retrospective" element={<Retrospective />} />
            <Route path="messages" element={<Messages />} />
            <Route path="messages/:channel" element={<Messages />} />
          </Route>
        </Route>
      </Routes>
    </Router>
  )
}

export default App
