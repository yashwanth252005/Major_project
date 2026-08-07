import { NavLink } from "react-router-dom";
import { BrainCircuit, LayoutDashboard, History } from "lucide-react";
import { motion } from "framer-motion";

const navLink = ({ isActive }) =>
  `relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
    isActive
      ? "text-white bg-white/10 shadow-lg"
      : "text-slate-400 hover:text-white hover:bg-white/5"
  }`;

export default function Navbar() {
  return (
    <motion.header
      initial={{ y: -35, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.45 }}
      className="sticky top-0 z-50 backdrop-blur-xl border-b border-white/10 bg-[#0A0E17]/80"
    >
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-8">

        {/* Logo */}

        <div className="flex items-center gap-4">

          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-blue-600 shadow-[0_10px_35px_rgba(79,107,255,.45)]">

            <BrainCircuit size={24} className="text-white" />

          </div>

          <div>

            <h1 className="text-xl font-bold tracking-tight gradient-text">
              NeuroScan XAI
            </h1>

            <p className="text-xs tracking-[0.25em] uppercase text-slate-400">
              AI Brain MRI Analysis
            </p>

          </div>

        </div>

        {/* Navigation */}

        <nav className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-2">

          <NavLink to="/" className={navLink}>
            <LayoutDashboard size={17} />
            Dashboard
          </NavLink>

          <NavLink to="/history" className={navLink}>
            <History size={17} />
            History
          </NavLink>

        </nav>

      </div>
    </motion.header>
  );
}