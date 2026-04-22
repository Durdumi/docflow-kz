import { useState } from "react";
import {
  Avatar,
  Badge,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { MailOutlined, PlusOutlined, StopOutlined, UserOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { usersApi } from "@/api/users";
import { useAuthStore } from "@/store/authStore";
import type { User } from "@/types";

const { Title, Text } = Typography;

const ROLE_CONFIG: Record<string, { color: string; label: string }> = {
  super_admin: { color: "red",     label: "Супер-админ" },
  org_admin:   { color: "blue",    label: "Администратор" },
  manager:     { color: "green",   label: "Менеджер" },
  user:        { color: "default", label: "Пользователь" },
};

const ROLE_OPTIONS = [
  { value: "org_admin", label: "Администратор" },
  { value: "manager",   label: "Менеджер" },
  { value: "user",      label: "Пользователь" },
];

export const UsersPage = () => {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();
  const [inviteOpen, setInviteOpen] = useState(false);
  const [form] = Form.useForm();

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: usersApi.list,
  });

  const inviteMutation = useMutation({
    mutationFn: usersApi.invite,
    onSuccess: (newUser) => {
      message.success(
        `Пользователь ${newUser.email} добавлен. Сообщите ему временный пароль.`
      );
      setInviteOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err: any) =>
      message.error(err?.response?.data?.detail || "Ошибка"),
  });

  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) =>
      usersApi.changeRole(id, role),
    onSuccess: () => {
      message.success("Роль обновлена");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: usersApi.deactivate,
    onSuccess: () => {
      message.success("Пользователь деактивирован");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });

  const isAdmin =
    currentUser?.role === "org_admin" || currentUser?.role === "super_admin";

  const columns = [
    {
      title: "Пользователь",
      key: "user",
      render: (_: unknown, record: User) => (
        <Space>
          <Avatar
            icon={<UserOutlined />}
            src={record.avatar_url}
            style={{ backgroundColor: "#1677ff" }}
          />
          <div>
            <Text strong>
              {record.last_name} {record.first_name}
              {record.id === currentUser?.id && (
                <Tag color="blue" style={{ marginLeft: 8, fontSize: 11 }}>
                  Вы
                </Tag>
              )}
            </Text>
            <br />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.email}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: "Роль",
      dataIndex: "role",
      key: "role",
      render: (role: string, record: User) => {
        if (!isAdmin || record.id === currentUser?.id) {
          const cfg = ROLE_CONFIG[role] || { color: "default", label: role };
          return <Tag color={cfg.color}>{cfg.label}</Tag>;
        }
        return (
          <Select
            value={role}
            size="small"
            style={{ width: 150 }}
            options={ROLE_OPTIONS}
            onChange={(val) => roleMutation.mutate({ id: record.id, role: val })}
          />
        );
      },
    },
    {
      title: "Статус",
      dataIndex: "is_verified",
      key: "status",
      render: (verified: boolean) => (
        <Badge
          status={verified ? "success" : "warning"}
          text={verified ? "Подтверждён" : "Ожидает входа"}
        />
      ),
    },
    {
      title: "Дата добавления",
      dataIndex: "created_at",
      key: "created_at",
      render: (d: string) => new Date(d).toLocaleDateString("ru-RU"),
    },
    ...(isAdmin
      ? [
          {
            title: "Действия",
            key: "actions",
            render: (_: unknown, record: User) => {
              if (record.id === currentUser?.id) return null;
              return (
                <Popconfirm
                  title="Деактивировать пользователя?"
                  description="Пользователь потеряет доступ к системе"
                  onConfirm={() => deactivateMutation.mutate(record.id)}
                  okText="Да"
                  cancelText="Нет"
                  okButtonProps={{ danger: true }}
                >
                  <Button size="small" danger icon={<StopOutlined />}>
                    Деактивировать
                  </Button>
                </Popconfirm>
              );
            },
          },
        ]
      : []),
  ];

  return (
    <div>
      <div
        style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}
      >
        <div>
          <Title level={3} style={{ margin: 0 }}>
            Пользователи
          </Title>
          <Text type="secondary">Управление доступом в организации</Text>
        </div>
        {isAdmin && (
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setInviteOpen(true)}
          >
            Добавить пользователя
          </Button>
        )}
      </div>

      <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={false}
          locale={{ emptyText: "Пользователей нет" }}
        />
      </Card>

      <Modal
        title="Добавить пользователя"
        open={inviteOpen}
        onCancel={() => {
          setInviteOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        confirmLoading={inviteMutation.isPending}
        okText="Добавить"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(v) => inviteMutation.mutate(v)}
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="email"
            label="Email"
            rules={[{ required: true, type: "email", message: "Введите корректный email" }]}
          >
            <Input prefix={<MailOutlined />} placeholder="user@company.kz" />
          </Form.Item>
          <Form.Item
            name="last_name"
            label="Фамилия"
            rules={[{ required: true, message: "Введите фамилию" }]}
          >
            <Input placeholder="Иванов" />
          </Form.Item>
          <Form.Item
            name="first_name"
            label="Имя"
            rules={[{ required: true, message: "Введите имя" }]}
          >
            <Input placeholder="Иван" />
          </Form.Item>
          <Form.Item name="role" label="Роль" initialValue="user">
            <Select options={ROLE_OPTIONS} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
