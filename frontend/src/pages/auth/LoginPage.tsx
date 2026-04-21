import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Alert, Button, Card, Divider, Form, Input, Typography } from "antd";
import { LockOutlined, MailOutlined } from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";
import type { LoginRequest } from "@/types";

const { Title, Text } = Typography;

export const LoginPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFinish = async (values: LoginRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.login(values);
      login(response.access_token, response.refresh_token, response.user);
      navigate("/dashboard");
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Ошибка входа. Проверьте данные.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%)",
        padding: 24,
      }}
    >
      <Card
        style={{ width: "100%", maxWidth: 420, boxShadow: "0 8px 32px rgba(0,0,0,0.08)" }}
        bordered={false}
      >
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <Title level={2} style={{ marginBottom: 4 }}>
            DocFlow KZ
          </Title>
          <Text type="secondary">{t("auth.loginTitle")}</Text>
        </div>

        {error && (
          <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />
        )}

        <Form name="login" onFinish={onFinish} layout="vertical" size="large">
          <Form.Item
            name="email"
            label={t("auth.email")}
            rules={[
              { required: true, message: "Введите email" },
              { type: "email", message: "Некорректный email" },
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="your@email.com" />
          </Form.Item>

          <Form.Item
            name="password"
            label={t("auth.password")}
            rules={[{ required: true, message: "Введите пароль" }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="••••••••" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 12 }}>
            <Button type="primary" htmlType="submit" loading={loading} block>
              {t("auth.login")}
            </Button>
          </Form.Item>
        </Form>

        <Divider style={{ margin: "12px 0" }} />

        <div style={{ textAlign: "center" }}>
          <Text type="secondary">{t("auth.noAccount")} </Text>
          <Link to="/register">{t("auth.register")}</Link>
        </div>
      </Card>
    </div>
  );
};
