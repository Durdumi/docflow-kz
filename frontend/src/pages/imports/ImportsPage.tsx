import { useState } from "react";
import {
  Badge,
  Button,
  Card,
  Form,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from "antd";
import {
  DeleteOutlined,
  FileExcelOutlined,
  FileOutlined,
  InboxOutlined,
  PlusOutlined,
  EyeOutlined,
} from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { importsApi } from "@/api/imports";
import type { UploadFile } from "antd";

const { Title, Text } = Typography;
const { Dragger } = Upload;

const SOURCE_ICON: Record<string, React.ReactNode> = {
  excel: <FileExcelOutlined style={{ color: "#52c41a" }} />,
  csv: <FileOutlined style={{ color: "#1677ff" }} />,
  json: <FileOutlined style={{ color: "#faad14" }} />,
};

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  pending:    { color: "default",    label: "Ожидает" },
  processing: { color: "processing", label: "Обработка" },
  done:       { color: "success",    label: "Готово" },
  failed:     { color: "error",      label: "Ошибка" },
};

const CATEGORIES = [
  { value: "salary",  label: "Зарплата" },
  { value: "finance", label: "Финансы" },
  { value: "hr",      label: "Кадры" },
  { value: "sales",   label: "Продажи" },
  { value: "stock",   label: "Склад / остатки" },
  { value: "other",   label: "Прочее" },
];

export const ImportsPage = () => {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [previewImport, setPreviewImport] = useState<any>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ["imports"],
    queryFn: () => importsApi.list(),
  });

  const uploadMutation = useMutation({
    mutationFn: ({
      file,
      name,
      category,
    }: {
      file: File;
      name: string;
      category?: string;
    }) => importsApi.upload(file, name, category),
    onSuccess: (result) => {
      message.success(`Импортировано ${result.row_count} строк`);
      setModalOpen(false);
      setFileList([]);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ["imports"] });
    },
    onError: (err: any) => {
      message.error(err?.response?.data?.detail || "Ошибка при импорте");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: importsApi.delete,
    onSuccess: () => {
      message.success("Удалено");
      queryClient.invalidateQueries({ queryKey: ["imports"] });
    },
  });

  const openPreview = async (record: any) => {
    const detail = await importsApi.getById(record.id);
    setPreviewImport(detail);
    setPreviewOpen(true);
  };

  const onFinish = (values: any) => {
    const file = fileList[0]?.originFileObj;
    if (!file) {
      message.error("Выберите файл");
      return;
    }
    uploadMutation.mutate({ file, name: values.name, category: values.category });
  };

  const columns = [
    {
      title: "Название",
      dataIndex: "name",
      key: "name",
      render: (text: string, record: any) => (
        <Space>
          {SOURCE_ICON[record.source_type] || <FileOutlined />}
          <Text strong>{text}</Text>
        </Space>
      ),
    },
    {
      title: "Файл",
      dataIndex: "original_filename",
      key: "original_filename",
      render: (name: string) => (
        <Text type="secondary" style={{ fontSize: 12 }}>
          {name}
        </Text>
      ),
    },
    {
      title: "Категория",
      dataIndex: "category",
      key: "category",
      render: (cat: string) => {
        const label = CATEGORIES.find((c) => c.value === cat)?.label || cat;
        return cat ? <Tag>{label}</Tag> : "—";
      },
    },
    {
      title: "Строк",
      dataIndex: "row_count",
      key: "row_count",
      render: (n: number) => <Text strong>{n.toLocaleString("ru-RU")}</Text>,
    },
    {
      title: "Статус",
      dataIndex: "status",
      key: "status",
      render: (status: string) => {
        const cfg = STATUS_CONFIG[status] || { color: "default", label: status };
        return <Badge status={cfg.color as any} text={cfg.label} />;
      },
    },
    {
      title: "Дата",
      dataIndex: "created_at",
      key: "created_at",
      render: (d: string) => new Date(d).toLocaleString("ru-RU"),
    },
    {
      title: "Действия",
      key: "actions",
      render: (_: any, record: any) => (
        <Space>
          <Button
            size="small"
            icon={<EyeOutlined />}
            onClick={() => openPreview(record)}
          >
            Просмотр
          </Button>
          <Popconfirm
            title="Удалить импорт?"
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const previewColumns = (previewImport?.columns || []).map((col: string) => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    render: (val: any) => val || "—",
  }));

  const items = data?.items || [];

  return (
    <div>
      <div
        style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}
      >
        <div>
          <Title level={3} style={{ margin: 0 }}>
            Импорт данных
          </Title>
          <Text type="secondary">
            Загружайте Excel, CSV или JSON файлы — данные сохраняются и доступны для
            отчётов
          </Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalOpen(true)}
        >
          Загрузить файл
        </Button>
      </div>

      {!isLoading && items.length === 0 ? (
        <Card
          bordered={false}
          style={{
            textAlign: "center",
            padding: 48,
            marginBottom: 24,
            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
          }}
        >
          <InboxOutlined style={{ fontSize: 48, color: "#d9d9d9", marginBottom: 16 }} />
          <Title level={4} style={{ color: "#999" }}>
            Нет импортированных данных
          </Title>
          <Text type="secondary">
            Загрузите Excel или CSV файл с данными из 1С, банка или любого другого
            источника
          </Text>
          <br />
          <br />
          <Button type="primary" onClick={() => setModalOpen(true)}>
            Загрузить первый файл
          </Button>
        </Card>
      ) : (
        <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
          <Table
            dataSource={items}
            columns={columns}
            rowKey="id"
            loading={isLoading}
            pagination={{ pageSize: 20, showTotal: (t) => `Всего: ${t}` }}
          />
        </Card>
      )}

      {/* Upload modal */}
      <Modal
        title="Загрузить файл"
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setFileList([]);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        confirmLoading={uploadMutation.isPending}
        okText="Импортировать"
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={onFinish} style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="Название импорта"
            rules={[{ required: true, message: "Введите название" }]}
          >
            <input
              className="ant-input"
              placeholder="Например: Зарплата апрель 2026"
              style={{
                width: "100%",
                padding: "7px 11px",
                borderRadius: 8,
                border: "1px solid #d9d9d9",
                fontSize: 14,
              }}
              onChange={(e) => form.setFieldValue("name", e.target.value)}
            />
          </Form.Item>

          <Form.Item name="category" label="Категория">
            <Select
              placeholder="Выберите категорию"
              options={CATEGORIES}
              allowClear
            />
          </Form.Item>

          <Form.Item label="Файл" required>
            <Dragger
              fileList={fileList}
              beforeUpload={() => false}
              onChange={({ fileList: fl }) => setFileList(fl.slice(-1))}
              accept=".xlsx,.xls,.csv,.json"
              maxCount={1}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">
                Перетащите файл или нажмите для выбора
              </p>
              <p className="ant-upload-hint">
                Поддерживается: Excel (.xlsx, .xls), CSV, JSON — до 10 MB
              </p>
            </Dragger>
          </Form.Item>
        </Form>
      </Modal>

      {/* Preview modal */}
      <Modal
        title={
          <Space>
            {previewImport && SOURCE_ICON[previewImport.source_type]}
            {previewImport?.name}
            <Tag>{previewImport?.row_count?.toLocaleString("ru-RU")} строк</Tag>
          </Space>
        }
        open={previewOpen}
        onCancel={() => {
          setPreviewOpen(false);
          setPreviewImport(null);
        }}
        footer={null}
        width={900}
      >
        {previewImport && (
          <div>
            <Space style={{ marginBottom: 12 }}>
              <Text type="secondary">Файл: {previewImport.original_filename}</Text>
              <Text type="secondary">
                Загружен:{" "}
                {new Date(previewImport.created_at).toLocaleString("ru-RU")}
              </Text>
            </Space>
            <Text
              type="secondary"
              style={{ display: "block", marginBottom: 8 }}
            >
              Показаны первые 10 строк из {previewImport.row_count}
            </Text>
            <div style={{ overflowX: "auto" }}>
              <Table
                dataSource={previewImport.preview_data}
                columns={previewColumns}
                rowKey={(_: any, idx: any) => String(idx)}
                pagination={false}
                size="small"
                scroll={{ x: "max-content" }}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ImportsPage;
