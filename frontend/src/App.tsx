import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import DatasetsPage from "./pages/DatasetsPage";
import DatasetDetailPage from "./pages/DatasetDetailPage";
import RunsPage from "./pages/RunsPage";
import RunDetailPage from "./pages/RunDetailPage";
import { getAccessToken } from "./api/client";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const token = getAccessToken();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 1200, margin: "0 auto", padding: 16, width: "100%", boxSizing: "border-box"}}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
          paddingBottom: 12,
          borderBottom: "1px solid #ddd",
        }}
      >
        <h1 style={{ margin: 0, fontSize: 24 }}>Backtester</h1>
        <nav style={{ display: "flex", gap: 12 }}>
          <Link to="/datasets">Datasets</Link>
          <Link to="/runs">Runs</Link>
        </nav>
      </header>
      {children}
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/datasets"
        element={
          <RequireAuth>
            <Layout>
              <DatasetsPage />
            </Layout>
          </RequireAuth>
        }
      />

      <Route
        path="/datasets/:datasetId"
        element={
          <RequireAuth>
            <Layout>
              <DatasetDetailPage />
            </Layout>
          </RequireAuth>
        }
      />

      <Route
        path="/runs"
        element={
          <RequireAuth>
            <Layout>
              <RunsPage />
            </Layout>
          </RequireAuth>
        }
      />

      <Route
        path="/runs/:runId"
        element={
          <RequireAuth>
            <Layout>
              <RunDetailPage />
            </Layout>
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/datasets" replace />} />
    </Routes>
  );
}