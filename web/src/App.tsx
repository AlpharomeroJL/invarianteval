import { Link, Route, Routes } from "react-router-dom";
import { CaseDetail } from "./pages/CaseDetail";
import { Login } from "./pages/Login";
import { OnlineEval } from "./pages/OnlineEval";
import { Runs } from "./pages/Runs";
import { Settings } from "./pages/Settings";
import { Suites } from "./pages/Suites";

export default function App() {
  return (
    <div className="layout">
      <nav>
        <strong>InvariantEval</strong>
        <Link to="/">Runs</Link>
        <Link to="/online">Online Eval</Link>
        <Link to="/suites">Suites</Link>
        <Link to="/settings">Settings</Link>
        <Link to="/login">Login</Link>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Runs />} />
          <Route path="/runs/:runId/cases/:caseId" element={<CaseDetail />} />
          <Route path="/online" element={<OnlineEval />} />
          <Route path="/suites" element={<Suites />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </main>
    </div>
  );
}
