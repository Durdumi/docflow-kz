import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  message,
} from "antd";
import {
  DeleteOutlined,
  DownloadOutlined,
  FileTextOutlined,
  PlusOutlined,
  ReloadOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import type { ColumnsType } from "antd/es/table";
import { reportsApi } from "@/api/reports";
import type { Report, ReportCreate } from "@/types";

const { Title } = Typography;
const { RangePicker } = DatePicker;

const STATUS_CONFIG: Record<
  string,
  { color: "default" | "processing" | "success" | "error"; label: string }
> = {
  pending:    { color: "default",    label: "Ожидает" },
  generating: { color: "processing", label: "Генерируется" },
  ready:      { color: "success",    label: "Готов" },
  failed:     { color: "error",      label: "Ошибка" },
};

const TYPE_OPTIONS = [
  { value: "weekly",    label: "Еженедельный" },
  { value: "monthly",   label: "Ежемесячный" },
  { value: "quarterly", label: "Квартальный" },
  { value: "annual",    label: "Годовой" },
  { value: "custom",    label: "Произвольный" },
];

const FORMAT_OPTIONS = [
  { value: "pdf",   label: "PDF" },
  { value: "excel", label: "Excel (.xlsx)" },
];

interface FormValues {
  title: string;
  type: string;
  format: string;
  period?: [{ toISOString(): string }, { toISOString(): string }];
}

export const ReportsPage = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [form] = Form.useForm<FormValues>();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["reports"],
    queryFn: () => reportsApi.list(),
    // Автообновление пока есть pending/generating отчёты
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      const hasActive = items.some(
        (r) => r.status === "pending" || r.status === "generating"
      );
      return hasActive ? 3000 : false;
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload: ReportCreate) => reportsApi.create(payload),
    onSuccess: () => {
      message.success("Отчёт поставлен в очередь на генерацию");
      setModalOpen(false);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
    onError: () => message.error("Ошибка при создании отчёта"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => {
      message.success("Отчёт удалён");
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
    onError: () => message.error("Ошибка при удалении"),
  });

  const handleDownload = async (record: Report) => {
    setDownloadingId(record.id);
    try {
      const blob = await reportsApi.download(record.id);
      const ext = record.format === "excel" ? "xlsx" : record.format;
      const filename = `${record.title}.${ext}`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      message.error("Не удалось скачать файл");
    } finally {
      setDownloadingId(null);
    }
  };

  const handleFinish = (values: FormValues) => {
    const [periodFrom, periodTo] = values.period ?? [];
    createMutation.mutate({
      title: values.title,
      type: values.type,
      format: (values.format ?? "pdf") as ReportCreate["format"],
      period_from: periodFrom?.toISOString(),
      period_to: periodTo?.toISOString(),
      parameters: {},
    });
  };

  const columns: ColumnsType<Report> = [
    {
      title: "Название",
      dataIndex: "title",
      key: "title",
      render: (text: string) => (
        <Space>
          <FileTextOutlined />
          {text}
        </Space>
      ),
    },
    {
      title: "Тип",
      dataIndex: "type",
      key: "type",
      width: 140,
      render: (type: string) =>
        TYPE_OPTIONS.find((o) => o.value === type)?.label ?? type,
    },
    {
      title: "Формат",
      dataIndex: "format",
      key: "format",
      width: 90,
      render: (fmt: string) => <Tag>{fmt.toUpperCase()}</Tag>,
    },
    {
      title: t("common.status"),
      dataIndex: "status",
      key: "status",
      width: 160,
      render: (status: string, record: Report) => {
        const cfg = STATUS_CONFIG[status] ?? { color: "default", label: status };
        return (
          <Space>
            <Badge status={cfg.color} text={cfg.label} />
            {status === "failed" && record.error_message && (
              <Tooltip title={record.error_message}>
                <WarningOutlined style={{ color: "#ff4d4f" }} />
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: "Размер",
      dataIndex: "file_size",
      key: "file_size",
      width: 100,
      render: (size?: number) =>
        size ? `${(size / 1024).toFixed(1)} KB` : "—",
    },
    {
      title: "Создан",
      dataIndex: "created_at",
      key: "created_at",
      width: 160,
      render: (d: string) => new Date(d).toLocaleString("ru-RU"),
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: 120,
      render: (_: unknown, record: Report) => (
        <Space>
          {record.status === "ready" && record.file_url && (
            <Button
              size="small"
              icon={<DownloadOutlined />}
              loading={downloadingId === record.id}
              onClick={() => handleDownload(record)}
            >
              {t("reports.download")}
            </Button>
          )}
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => deleteMutation.mutate(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          {t("reports.title")}
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            Обновить
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalOpen(true)}
          >
            {t("reports.generate")}
          </Button>
        </Space>
      </div>

      <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={data?.items ?? []}
          loading={isLoading}
          pagination={{ pageSize: 20, showTotal: (total) => `Всего: ${total}` }}
        />
      </Card>

      <Modal
        title={t("reports.generate")}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        okText="Сформировать"
        cancelText={t("common.cancel")}
        destroyOnClose
      >
        <Form
          form={form}
          onFinish={handleFinish}
          layout="vertical"
          style={{ marginTop: 16 }}
        >
          <Form.Item
            name="title"
            label="Название отчёта"
            rules={[{ required: true, message: "Введите название" }]}
          >
            <Input
              placeholder="Например: Ежемесячный отчёт за апрель"
              maxLength={255}
            />
          </Form.Item>

          <Form.Item
            name="type"
            label="Тип отчёта"
            rules={[{ required: true, message: "Выберите тип" }]}
          >
            <Select options={TYPE_OPTIONS} placeholder="Выберите тип" />
          </Form.Item>

          <Form.Item name="format" label="Формат" initialValue="pdf">
            <Select options={FORMAT_OPTIONS} />
          </Form.Item>

          <Form.Item name="period" label="Период">
            <RangePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ReportsPage;
