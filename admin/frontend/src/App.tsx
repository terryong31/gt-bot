import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Users from './pages/Users'
import Invites from './pages/Invites'
import Logs from './pages/Logs'
import Conversation from './pages/Conversation'
import Landing from './pages/Landing'
import Privacy from './pages/Privacy'
import Terms from './pages/Terms'
import PublicLayout from './components/layout/PublicLayout'

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                {/* Public pages wrapped in professional layout */}
                <Route element={<PublicLayout />}>
                    <Route path="/" element={<Landing />} />
                    <Route path="/privacy" element={<Privacy />} />
                    <Route path="/terms" element={<Terms />} />
                    <Route path="/login" element={<Login />} />
                </Route>

                {/* Admin panel (protected) */}
                <Route element={<Dashboard />}>
                    <Route path="/users" element={<Users />} />
                    <Route path="/invites" element={<Invites />} />
                    <Route path="/logs" element={<Logs />} />
                    <Route path="/logs/conversation/:userId" element={<Conversation />} />
                </Route>
            </Routes>
        </BrowserRouter>
    )
}
