import { Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ConfigProvider, Spin, theme } from "antd";
import ruRU from "antd/locale/ru_RU";
import kkKZ from "antd/locale/kk_KZ";
import { useTranslation } from "react-i18next";
import { useThemeStore } from "@/store/themeStore";
import "@/i18n";

import { ProtectedRoute } from "@/components/common/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/pages/auth/LoginPage";
import { RegisterPage } from "@/pages/auth/RegisterPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { DocumentsPage } from "@/pages/documents/DocumentsPage";
import { CreateDocumentPage } from "@/pages/documents/CreateDocumentPage";
import { TemplatesPage } from "@/pages/templates/TemplatesPage";
import { ReportsPage } from "@/pages/reports/ReportsPage";
import { TaskBoardPage } from "@/pages/tasks/TaskBoardPage";
import { CalendarPage } from "@/pages/calendar/CalendarPage";
import { ImportsPage } from "@/pages/imports/ImportsPage";
import { UsersPage } from "@/pages/users/UsersPage";
import { SettingsPage } from "@/pages/settings/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 1000 * 60 * 5, retry: 1, refetchOnWindowFocus: false },
  },
});

const antdLocales: Record<string, typeof ruRU> = { ru: ruRU, kk: kkKZ };

function App() {
  const { i18n } = useTranslation();
  const { isDark, accentColor } = useThemeStore();
  const locale = antdLocales[i18n.language] || ruRU;

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={locale}
        theme={{
          algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
          token: {
            colorPrimary: accentColor,
            borderRadius: 10,
            fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            colorBgBase: isDark ? "#141414" : "#ffffff",
            colorBgContainer: isDark ? "#1e1e1e" : "#ffffff",
            colorBgElevated: isDark ? "#252525" : "#ffffff",
            colorBgLayout: isDark ? "#111111" : "#f5f7fa",
            boxShadow: isDark
              ? "0 2px 8px rgba(0,0,0,0.4)"
              : "0 2px 8px rgba(0,0,0,0.06)",
          },
          components: {
            Layout: {
              siderBg: isDark ? "#1e1e1e" : "#ffffff",
              bodyBg: isDark ? "#111111" : "#f5f7fa",
            },
            Menu: {
              itemBg: isDark ? "#1e1e1e" : "#ffffff",
              darkItemBg: "#1e1e1e",
            },
            Card: {
              colorBgContainer: isDark ? "#1e1e1e" : "#ffffff",
            },
          },
        }}
      >
        <style>{`
          body {
            background: ${isDark ? "#111111" : "#f5f7fa"} !important;
            transition: background 0.3s ease;
          }
          * { transition: background-color 0.2s ease, border-color 0.2s ease; }
        `}</style>

        <BrowserRouter>
          <Suspense fallback={
            <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Spin size="large" />
            </div>
          }>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/documents" element={<DocumentsPage />} />
                  <Route path="/documents/create" element={<CreateDocumentPage />} />
                  <Route path="/templates" element={<TemplatesPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                  <Route path="/tasks" element={<TaskBoardPage />} />
                  <Route path="/calendar" element={<CalendarPage />} />
                  <Route path="/imports" element={<ImportsPage />} />
                  <Route path="/users" element={<UsersPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Route>
              </Route>

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
