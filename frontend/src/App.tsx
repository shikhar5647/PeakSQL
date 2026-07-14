import { BrowserRouter, Route, Routes } from "react-router-dom";
import Nav from "./components/Nav";
import Home from "./pages/Home";
import Studio from "./pages/Studio";
import Team from "./pages/Team";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Nav />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/studio" element={<Studio />} />
          <Route path="/team" element={<Team />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
