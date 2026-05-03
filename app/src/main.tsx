import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import App from "./App";
import "./index.css";
import SongDetailPage from "./pages/SongDetailPage";

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/songs/:songId" element={<SongDetailPage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
