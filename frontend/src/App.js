import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import ProtectedRoute from "@/components/ProtectedRoute";
import Home from "@/pages/Home";
import Submit from "@/pages/Submit";
import EntryDetail from "@/pages/EntryDetail";
import ModLogin from "@/pages/ModLogin";
import ModDashboard from "@/pages/ModDashboard";

function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/submit" element={<Submit />} />
      <Route path="/entry/:slug" element={<EntryDetail />} />
      <Route path="/mod/login" element={<ModLogin />} />
      <Route
        path="/mod/dashboard"
        element={
          <ProtectedRoute>
            <ModDashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AuthProvider>
          <AppRouter />
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

export default App;
