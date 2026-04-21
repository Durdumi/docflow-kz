import { Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ConfigProvider, Spin, theme } from "antd";
import ruRU from "antd/locale/ru_RU";
import kkKZ from "antd/locale/kk_KZ";
import { useTranslation } from "react-i18next";
import "@/i18n";

import { ProtectedRoute } from "@/components/common/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { DocumentsPage } from "@/pages/documents/DocumentsPage";
import { CreateDocumentPage } from "@/pages/documents/CreateDocumentPage";
import { TemplatesPage } from "@/pages/templates/TemplatesPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 минут
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const antdLocales: Record<string, typeof ruRU> = {
  ru: ruRU,
  kk: kkKZ,
};

function App() {
  const { i18n } = useTranslation();
  const locale = antdLocales[i18n.language] || ruRU;

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={locale}
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: "#1677ff",
            borderRadius: 8,
            fontFamily:
              "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          },
          components: {
            Layout: { siderBg: "#ffffff" },
            Menu: { itemBg: "#ffffff" },
          },
        }}
      >
        <BrowserRouter>
          <Suspense
            fallback={
              <div
                style={{
                  height: "100vh",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Spin size="large" />
              </div>
            }
          >
            <Routes>
              {/* ─── Public routes ──────────────────────────── */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* ─── Protected routes ───────────────────────── */}
              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/documents" element={<DocumentsPage />} />
                  <Route path="/documents/create" element={<CreateDocumentPage />} />
                  <Route path="/templates" element={<TemplatesPage />} />
                  {/* <Route path="/reports/*" element={<ReportsPage />} /> */}
                </Route>
              </Route>

              {/* ─── Redirect root ──────────────────────────── */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ConfigProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
