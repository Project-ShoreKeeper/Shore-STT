import App from "@Shore/App";
import PageMain from "@Shore/pages/Main";
import { Routes, Route } from "react-router-dom";

export default function PublicRoutes() {
  return (
    <Routes>
      <Route path="/" element={<PageMain />} />
    </Routes>
  );
}
