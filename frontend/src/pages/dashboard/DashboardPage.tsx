import { Card, Col, Row, Statistic, Table, Tag, Typography } from "antd";
import {
  FileOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
} from "@ant-design/icons";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";

const { Title, Text } = Typography;

// Временные mock данные — потом заменим на TanStack Query
const mockRecentDocs = [
  { id: "1", title: "Договор №123", category: "HR", status: "active", date: "2024-11-20" },
  { id: "2", title: "Приказ о командировке", category: "HR", status: "draft", date: "2024-11-19" },
  { id: "3", title: "Акт выполненных работ", category: "Проект", status: "active", date: "2024-11-18" },
  { id: "4", title: "Квартальный отчёт Q3", category: "Финансы", status: "archived", date: "2024-11-15" },
];

const statusConfig: Record<string, { color: string; label: string }> = {
  active: { color: "green", label: "Активный" },
  draft: { color: "orange", label: "Черновик" },
  archived: { color: "default", label: "Архив" },
};

const columns = [
  { title: "Название", dataIndex: "title", key: "title" },
  { title: "Категория", dataIndex: "category", key: "category" },
  {
    title: "Статус",
    dataIndex: "status",
    key: "status",
    render: (status: string) => {
      const cfg = statusConfig[status] || { color: "default", label: status };
      return <Tag color={cfg.color}>{cfg.label}</Tag>;
    },
  },
  { title: "Дата", dataIndex: "date", key: "date" },
];

export const DashboardPage = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  return (
    <div>
      {/* Welcome */}
      <div style={{ marginBottom: 24 }}>
        <Title level={3} style={{ marginBottom: 4 }}>
          {t("dashboard.welcome")}, {user?.first_name}! 👋
        </Title>
        <Text type="secondary">Вот что происходит в вашей организации сегодня</Text>
      </div>

      {/* Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title={t("dashboard.totalDocuments")}
              value={47}
              prefix={<FileOutlined style={{ color: "#1677ff" }} />}
              valueStyle={{ color: "#1677ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title={t("dashboard.totalReports")}
              value={12}
              prefix={<FileTextOutlined style={{ color: "#52c41a" }} />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title={t("dashboard.pendingTasks")}
              value={3}
              prefix={<ClockCircleOutlined style={{ color: "#faad14" }} />}
              valueStyle={{ color: "#faad14" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title="Завершено за месяц"
              value={28}
              prefix={<CheckCircleOutlined style={{ color: "#13c2c2" }} />}
              valueStyle={{ color: "#13c2c2" }}
            />
          </Card>
        </Col>
      </Row>

      {/* Recent Documents */}
      <Card
        title={t("dashboard.recentDocuments")}
        bordered={false}
        style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
        extra={<a href="/documents">Все документы →</a>}
      >
        <Table
          dataSource={mockRecentDocs}
          columns={columns}
          rowKey="id"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};
