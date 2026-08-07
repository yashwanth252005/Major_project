import { NavLink } from "react-router-dom";

const linkClasses = ({ isActive }) =>
  `px-3 py-1.5 rounded-full text-sm font-medium transition ${
    isActive ? "bg-brand-500 text-white" : "text-slate-300 hover:text-white"
  }`;

export default function Navbar() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-brand-400 to-brand-600" />
          <span className="font-semibold tracking-tight">Brain Tumor XAI</span>
        </div>
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkClasses}>
            Dashboard
          </NavLink>
          <NavLink to="/history" className={linkClasses}>
            History
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
