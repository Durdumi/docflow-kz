import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Avatar,
  Badge,
  Dropdown,
  Layout,
  Menu,
  Popover,
  Space,
  Switch,
  Tooltip,
  Typography,
  theme,
} from "antd";
import {
  BellOutlined,
  BgColorsOutlined,
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
  MoonOutlined,
  SettingOutlined,
  SunOutlined,
  TeamOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { useThemeStore, ACCENT_COLORS } from "@/store/themeStore";

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
  const { isDark, accentColor, toggleDark, setAccentColor } = useThemeStore();

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
      onClick: () => navigate("/settings"),
    },
    {
      key: "appearance",
      icon: <BgColorsOutlined />,
      label: "Внешний вид",
      onClick: () => navigate("/settings?tab=appearance"),
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

  const colorPickerContent = (
    <div style={{ padding: 8 }}>
      <div style={{ fontSize: 12, color: "#999", marginBottom: 8 }}>
        Цвет интерфейса
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", maxWidth: 200 }}>
        {ACCENT_COLORS.map((color) => (
          <Tooltip key={color.value} title={color.name}>
            <div
              onClick={() => setAccentColor(color.value)}
              style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                background: color.value,
                cursor: "pointer",
                border: accentColor === color.value
                  ? "3px solid #fff"
                  : "2px solid transparent",
                boxShadow: accentColor === color.value
                  ? `0 0 0 2px ${color.value}`
                  : "none",
                transition: "all 0.2s",
              }}
            />
          </Tooltip>
        ))}
      </div>
    </div>
  );

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
            {/* Color picker */}
            <Popover
              trigger="click"
              placement="bottomRight"
              content={colorPickerContent}
            >
              <Tooltip title="Цвет интерфейса">
                <BgColorsOutlined
                  style={{ fontSize: 18, cursor: "pointer", color: accentColor }}
                />
              </Tooltip>
            </Popover>

            {/* Dark mode toggle */}
            <Tooltip title={isDark ? "Светлая тема" : "Тёмная тема"}>
              <Switch
                checked={isDark}
                onChange={toggleDark}
                checkedChildren={<MoonOutlined />}
                unCheckedChildren={<SunOutlined />}
                size="small"
              />
            </Tooltip>

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
