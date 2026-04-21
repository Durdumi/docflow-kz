import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Alert,
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  Row,
  Steps,
  Typography,
} from "antd";
import {
  BankOutlined,
  LockOutlined,
  MailOutlined,
  PhoneOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";
import type { RegisterRequest } from "@/types";

const { Title, Text } = Typography;

export const RegisterPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { title: "Организация", description: "Данные компании" },
    { title: "Аккаунт", description: "Ваши данные" },
  ];

  const validateStep = async () => {
    const fieldsToValidate =
      currentStep === 0
        ? ["organization_name", "organization_email", "bin_number", "city"]
        : ["email", "password", "first_name", "last_name"];
    await form.validateFields(fieldsToValidate);
    setCurrentStep(1);
  };

  const onFinish = async (values: RegisterRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.register(values);
      login(response.access_token, response.refresh_token, response.user);
      navigate("/dashboard");
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Ошибка регистрации. Попробуйте снова.";
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
        style={{ width: "100%", maxWidth: 520, boxShadow: "0 8px 32px rgba(0,0,0,0.08)" }}
        bordered={false}
      >
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <Title level={2} style={{ marginBottom: 4 }}>
            DocFlow KZ
          </Title>
          <Text type="secondary">{t("auth.registerTitle")}</Text>
        </div>

        <Steps current={currentStep} items={steps} style={{ marginBottom: 28 }} size="small" />

        {error && (
          <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />
        )}

        <Form form={form} name="register" onFinish={onFinish} layout="vertical" size="large">
          {/* ─── Step 0: Organization ──────────────────────────── */}
          <div style={{ display: currentStep === 0 ? "block" : "none" }}>
            <Form.Item
              name="organization_name"
              label={t("auth.orgName")}
              rules={[{ required: true, message: "Введите название организации" }]}
            >
              <Input prefix={<BankOutlined />} placeholder="ТОО Моя Компания" />
            </Form.Item>

            <Form.Item
              name="organization_email"
              label={t("auth.orgEmail")}
              rules={[
                { required: true, message: "Введите email" },
                { type: "email", message: "Некорректный email" },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="info@company.kz" />
            </Form.Item>

            <Row gutter={12}>
              <Col span={12}>
                <Form.Item name="bin_number" label={t("auth.binNumber")}>
                  <Input placeholder="000000000000" maxLength={12} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="city" label={t("auth.city")}>
                  <Input placeholder="Алматы" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="organization_phone" label={t("auth.phone")}>
              <Input prefix={<PhoneOutlined />} placeholder="+7 (777) 000-00-00" />
            </Form.Item>

            <Button type="primary" block onClick={validateStep}>
              Далее
            </Button>
          </div>

          {/* ─── Step 1: User Account ──────────────────────────── */}
          <div style={{ display: currentStep === 1 ? "block" : "none" }}>
            <Row gutter={12}>
              <Col span={12}>
                <Form.Item
                  name="last_name"
                  label={t("auth.lastName")}
                  rules={[{ required: true, message: "Введите фамилию" }]}
                >
                  <Input prefix={<UserOutlined />} placeholder="Иванов" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  name="first_name"
                  label={t("auth.firstName")}
                  rules={[{ required: true, message: "Введите имя" }]}
                >
                  <Input placeholder="Иван" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="middle_name" label={t("auth.middleName")}>
              <Input placeholder="Иванович" />
            </Form.Item>

            <Form.Item
              name="email"
              label={t("auth.email")}
              rules={[
                { required: true, message: "Введите email" },
                { type: "email", message: "Некорректный email" },
              ]}
            >
              <Input prefix={<MailOutlined />} placeholder="admin@company.kz" />
            </Form.Item>

            <Form.Item
              name="password"
              label={t("auth.password")}
              rules={[
                { required: true, message: "Введите пароль" },
                { min: 8, message: "Минимум 8 символов" },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} placeholder="Минимум 8 символов" />
            </Form.Item>

            <Row gutter={12}>
              <Col span={12}>
                <Button block onClick={() => setCurrentStep(0)}>
                  Назад
                </Button>
              </Col>
              <Col span={12}>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  Зарегистрироваться
                </Button>
              </Col>
            </Row>
          </div>
        </Form>

        <Divider style={{ margin: "16px 0" }} />

        <div style={{ textAlign: "center" }}>
          <Text type="secondary">{t("auth.hasAccount")} </Text>
          <Link to="/login">{t("auth.login")}</Link>
        </div>
      </Card>
    </div>
  );
};
