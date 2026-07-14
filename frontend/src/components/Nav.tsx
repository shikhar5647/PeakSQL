import { NavLink } from "react-router-dom";

export default function Nav() {
  return (
    <header className="topbar">
      <NavLink to="/" className="logo-link">
        <span className="logo">
          Peak<em>SQL</em>
        </span>
      </NavLink>
      <nav className="nav-links">
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Home
        </NavLink>
        <NavLink to="/studio" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Studio
        </NavLink>
        <NavLink to="/team" className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
          Team
        </NavLink>
      </nav>
      <span className="spacer" />
      <a className="nav-link ext" href="https://github.com/shikhar5647/PeakSQL" target="_blank" rel="noreferrer">
        GitHub ↗
      </a>
    </header>
  );
}
