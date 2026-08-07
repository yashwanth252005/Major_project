import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import History from "./pages/History.jsx";
import ScanDetail from "./pages/ScanDetail.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
          <Route path="/history/:id" element={<ScanDetail />} />
        </Routes>
      </main>
    </div>
  );
}
