import { useEffect } from "react";
import {
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  Row,
  Select,
  Space,
  Tabs,
  Typography,
  message,
} from "antd";
import { BankOutlined, UserOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { organizationsApi, usersApi } from "@/api/users";
import { useAuthStore } from "@/store/authStore";

const { Title, Text } = Typography;

export const SettingsPage = () => {
  const { user, updateUser } = useAuthStore();
  const queryClient = useQueryClient();
  const [profileForm] = Form.useForm();
  const [orgForm] = Form.useForm();

  const isAdmin =
    user?.role === "org_admin" || user?.role === "super_admin";

  const { data: org } = useQuery({
    queryKey: ["organization-me"],
    queryFn: organizationsApi.getMe,
    enabled: isAdmin,
  });

  useEffect(() => {
    if (user) {
      profileForm.setFieldsValue({
        first_name: user.first_name,
        last_name: user.last_name,
        middle_name: user.middle_name,
        phone: user.phone,
        telegram_chat_id: user.telegram_chat_id,
      });
    }
  }, [user, profileForm]);

  useEffect(() => {
    if (org) {
      orgForm.setFieldsValue({
        name: org.name,
        contact_email: org.contact_email,
        contact_phone: org.contact_phone,
        city: org.city,
        bin_number: org.bin_number,
        locale: org.locale,
        timezone: org.timezone,
      });
    }
  }, [org, orgForm]);

  const profileMutation = useMutation({
    mutationFn: usersApi.updateProfile,
    onSuccess: (updated) => {
      updateUser(updated);
      message.success("Профиль обновлён");
    },
    onError: () => message.error("Ошибка при обновлении"),
  });

  const orgMutation = useMutation({
    mutationFn: organizationsApi.updateMe,
    onSuccess: () => {
      message.success("Настройки организации сохранены");
      queryClient.invalidateQueries({ queryKey: ["organization-me"] });
    },
    onError: () => message.error("Ошибка при сохранении"),
  });

  const tabItems = [
    {
      key: "profile",
      label: (
        <Space>
          <UserOutlined />
          Профиль
        </Space>
      ),
      children: (
        <Form
          form={profileForm}
          layout="vertical"
          onFinish={(v) => profileMutation.mutate(v)}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="last_name"
                label="Фамилия"
                rules={[{ required: true, message: "Введите фамилию" }]}
              >
                <Input placeholder="Иванов" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="first_name"
                label="Имя"
                rules={[{ required: true, message: "Введите имя" }]}
              >
                <Input placeholder="Иван" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="middle_name" label="Отчество">
            <Input placeholder="Иванович" />
          </Form.Item>
          <Form.Item name="phone" label="Телефон">
            <Input placeholder="+7 (777) 000-00-00" />
          </Form.Item>
          <Form.Item
            name="telegram_chat_id"
            label="Telegram ID для уведомлений"
            extra={
              <>
                Напишите <b>/start</b> боту{" "}
                <a
                  href="https://t.me/DocFlowKZbot"
                  target="_blank"
                  rel="noreferrer"
                >
                  @DocFlowKZbot
                </a>{" "}
                чтобы получить ваш ID
              </>
            }
          >
            <Input placeholder="123456789" prefix="✈️" />
          </Form.Item>
          <Divider />
          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={profileMutation.isPending}
            >
              Сохранить профиль
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    ...(isAdmin
      ? [
          {
            key: "organization",
            label: (
              <Space>
                <BankOutlined />
                Организация
              </Space>
            ),
            children: (
              <Form
                form={orgForm}
                layout="vertical"
                onFinish={(v) => orgMutation.mutate(v)}
              >
                <Form.Item
                  name="name"
                  label="Название организации"
                  rules={[{ required: true, message: "Введите название" }]}
                >
                  <Input />
                </Form.Item>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="contact_email" label="Email организации">
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="contact_phone" label="Телефон">
                      <Input placeholder="+7 (727) 000-00-00" />
                    </Form.Item>
                  </Col>
                </Row>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="city" label="Город">
                      <Input placeholder="Алматы" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="bin_number" label="БИН">
                      <Input placeholder="000000000000" maxLength={12} />
                    </Form.Item>
                  </Col>
                </Row>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="locale" label="Язык интерфейса">
                      <Select
                        options={[
                          { value: "ru", label: "Русский" },
                          { value: "kk", label: "Қазақша" },
                          { value: "en", label: "English" },
                        ]}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="timezone" label="Часовой пояс">
                      <Select
                        options={[
                          { value: "Asia/Almaty",   label: "Алматы (UTC+5)" },
                          { value: "Asia/Astana",   label: "Астана (UTC+5)" },
                          { value: "Asia/Aqtobe",   label: "Актобе (UTC+5)" },
                          { value: "Europe/Moscow", label: "Москва (UTC+3)" },
                        ]}
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Divider />
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={orgMutation.isPending}
                >
                  Сохранить настройки
                </Button>
              </Form>
            ),
          },
        ]
      : []),
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>
          Настройки
        </Title>
        <Text type="secondary">
          {user?.last_name} {user?.first_name} · {user?.email}
        </Text>
      </div>

      <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
        <Tabs items={tabItems} />
      </Card>
    </div>
  );
};
