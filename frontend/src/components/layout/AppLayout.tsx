import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Avatar,
  Badge,
  Breadcrumb,
  Dropdown,
  Layout,
  Menu,
  Space,
  Typography,
  theme,
} from "antd";
import {
  BellOutlined,
  CalendarOutlined,
  CheckSquareOutlined,
  DashboardOutlined,
  FileOutlined,
  FileTextOutlined,
  GlobalOutlined,
  ImportOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  TeamOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const MENU_ITEMS = [
  { key: "/dashboard", icon: <DashboardOutlined />, labelKey: "nav.dashboard" },
  { key: "/documents", icon: <FileOutlined />, labelKey: "nav.documents" },
  { key: "/reports", icon: <FileTextOutlined />, labelKey: "nav.reports" },
  { key: "/templates", icon: <FileTextOutlined />, labelKey: "nav.templates" },
  { key: "/imports",   icon: <ImportOutlined />,     labelKey: "nav.imports" },
  { key: "/tasks",    icon: <CheckSquareOutlined />, labelKey: "nav.tasks" },
  { key: "/calendar", icon: <CalendarOutlined />,    labelKey: "nav.calendar" },
  { key: "/users",    icon: <TeamOutlined />,         labelKey: "nav.users", adminOnly: true },
  { key: "/settings", icon: <SettingOutlined />, labelKey: "nav.settings" },
];

export const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { token: colorToken } = theme.useToken();

  const isAdmin = user?.role === "org_admin" || user?.role === "super_admin";

  const visibleMenuItems = MENU_ITEMS.filter(
    (item) => !("adminOnly" in item && item.adminOnly) || isAdmin
  ).map((item) => ({
    key: item.key,
    icon: item.icon,
    label: <Link to={item.key}>{t(item.labelKey)}</Link>,
  }));

  const userMenuItems = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: t("nav.settings"),
      onClick: () => navigate("/settings/profile"),
    },
    {
      key: "lang-ru",
      icon: <GlobalOutlined />,
      label: "Русский",
      onClick: () => i18n.changeLanguage("ru"),
    },
    {
      key: "lang-kk",
      icon: <GlobalOutlined />,
      label: "Қазақша",
      onClick: () => i18n.changeLanguage("kk"),
    },
    { type: "divider" as const },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: t("auth.logout"),
      danger: true,
      onClick: logout,
    },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      {/* ─── Sidebar ──────────────────────────────────────────── */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        style={{
          background: colorToken.colorBgContainer,
          borderRight: `1px solid ${colorToken.colorBorderSecondary}`,
          position: "fixed",
          height: "100vh",
          left: 0,
          top: 0,
          zIndex: 100,
        }}
        width={220}
      >
        {/* Logo */}
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "flex-start",
            padding: collapsed ? 0 : "0 24px",
            borderBottom: `1px solid ${colorToken.colorBorderSecondary}`,
            overflow: "hidden",
          }}
        >
          <Text
            strong
            style={{
              fontSize: collapsed ? 18 : 20,
              color: colorToken.colorPrimary,
              whiteSpace: "nowrap",
            }}
          >
            {collapsed ? "DF" : "DocFlow KZ"}
          </Text>
        </div>

        {/* Navigation */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={visibleMenuItems}
          style={{ border: "none", marginTop: 8 }}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 220, transition: "margin 0.2s" }}>
        {/* ─── Header ─────────────────────────────────────────── */}
        <Header
          style={{
            padding: "0 24px",
            background: colorToken.colorBgContainer,
            borderBottom: `1px solid ${colorToken.colorBorderSecondary}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 99,
          }}
        >
          {/* Collapse button */}
          <span
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 18, cursor: "pointer", color: colorToken.colorTextSecondary }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </span>

          {/* Right side */}
          <Space size={16}>
            {/* Notifications */}
            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: 18, cursor: "pointer" }} />
            </Badge>

            {/* User menu */}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
              <Space style={{ cursor: "pointer" }}>
                <Avatar
                  size={32}
                  icon={<UserOutlined />}
                  src={user?.avatar_url}
                  style={{ backgroundColor: colorToken.colorPrimary }}
                />
                {!collapsed && (
                  <Text style={{ maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {user?.first_name} {user?.last_name}
                  </Text>
                )}
              </Space>
            </Dropdown>
          </Space>
        </Header>

        {/* ─── Content ────────────────────────────────────────── */}
        <Content style={{ padding: 24, minHeight: "calc(100vh - 64px)" }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};
