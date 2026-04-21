import { useNavigate } from "react-router-dom";
import {
  Badge,
  Button,
  Card,
  Col,
  Row,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileOutlined,
  FileTextOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useAuthStore } from "@/store/authStore";
import { dashboardApi } from "@/api/dashboard";

const { Title, Text } = Typography;

const DOC_STATUS: Record<string, { color: string; label: string }> = {
  draft:    { color: "orange",  label: "Черновик" },
  active:   { color: "green",   label: "Активный" },
  archived: { color: "default", label: "Архив" },
  deleted:  { color: "red",     label: "Удалён" },
};

const REPORT_STATUS: Record<
  string,
  { color: "default" | "processing" | "success" | "error"; label: string }
> = {
  pending:    { color: "default",    label: "Ожидает" },
  generating: { color: "processing", label: "Генерируется" },
  ready:      { color: "success",    label: "Готов" },
  failed:     { color: "error",      label: "Ошибка" },
};

export const DashboardPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.getStats,
    refetchInterval: 30_000,
  });

  const docColumns = [
    {
      title: "Название",
      dataIndex: "title",
      key: "title",
      ellipsis: true,
      render: (text: string) => (
        <a onClick={() => navigate("/documents")}>{text}</a>
      ),
    },
    {
      title: "Статус",
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (s: string) => {
        const cfg = DOC_STATUS[s] ?? { color: "default", label: s };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: "Дата",
      dataIndex: "created_at",
      key: "created_at",
      width: 100,
      render: (d: string) => new Date(d).toLocaleDateString("ru-RU"),
    },
  ];

  const reportColumns = [
    {
      title: "Название",
      dataIndex: "title",
      key: "title",
      ellipsis: true,
      render: (text: string) => (
        <a onClick={() => navigate("/reports")}>{text}</a>
      ),
    },
    {
      title: "Статус",
      dataIndex: "status",
      key: "status",
      width: 130,
      render: (s: string) => {
        const cfg = REPORT_STATUS[s] ?? { color: "default" as const, label: s };
        return <Badge status={cfg.color} text={cfg.label} />;
      },
    },
    {
      title: "Дата",
      dataIndex: "created_at",
      key: "created_at",
      width: 100,
      render: (d: string) => new Date(d).toLocaleDateString("ru-RU"),
    },
  ];

  if (isLoading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: 60 }}>
        <Spin size="large" />
      </div>
    );
  }

  const readyReports =
    stats?.recent_reports?.filter((r) => r.status === "ready").length ?? 0;

  return (
    <div>
      <div
        style={{
          marginBottom: 24,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <Title level={3} style={{ margin: 0 }}>
            {t("dashboard.welcome")}, {user?.first_name}!
          </Title>
          <Text type="secondary">
            {new Date().toLocaleDateString("ru-RU", {
              weekday: "long",
              day: "numeric",
              month: "long",
            })}
          </Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate("/documents/create")}
        >
          Новый документ
        </Button>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title="Всего документов"
              value={stats?.total_documents ?? 0}
              prefix={<FileOutlined style={{ color: "#1677ff" }} />}
              valueStyle={{ color: "#1677ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title="Отчётов всего"
              value={stats?.total_reports ?? 0}
              prefix={<FileTextOutlined style={{ color: "#52c41a" }} />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title="Ожидают генерации"
              value={stats?.pending_reports ?? 0}
              prefix={<ClockCircleOutlined style={{ color: "#faad14" }} />}
              valueStyle={{ color: "#faad14" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
            <Statistic
              title="Готовых отчётов"
              value={readyReports}
              prefix={<CheckCircleOutlined style={{ color: "#13c2c2" }} />}
              valueStyle={{ color: "#13c2c2" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card
            title={t("dashboard.recentDocuments")}
            bordered={false}
            style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
            extra={<a onClick={() => navigate("/documents")}>Все →</a>}
          >
            <Table
              dataSource={stats?.recent_documents ?? []}
              columns={docColumns}
              rowKey="id"
              pagination={false}
              size="small"
              locale={{ emptyText: "Документов пока нет" }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            title={t("dashboard.recentReports")}
            bordered={false}
            style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}
            extra={<a onClick={() => navigate("/reports")}>Все →</a>}
          >
            <Table
              dataSource={stats?.recent_reports ?? []}
              columns={reportColumns}
              rowKey="id"
              pagination={false}
              size="small"
              locale={{ emptyText: "Отчётов пока нет" }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
