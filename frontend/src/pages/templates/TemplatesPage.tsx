import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Button,
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
import {
  DeleteOutlined,
  EditOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnsType } from "antd/es/table";
import type { DocumentTemplate, TemplateField } from "@/types";
import {
  type CreateTemplateRequest,
  type UpdateTemplateRequest,
  templatesApi,
} from "@/api/documents";
import { TemplateFieldsEditor } from "@/components/documents/TemplateFieldsEditor";

const { Title, Text } = Typography;
const { Option } = Select;

const CATEGORIES = [
  { value: "contract", label: "Договор" },
  { value: "act", label: "Акт" },
  { value: "invoice", label: "Счёт / Накладная" },
  { value: "report", label: "Отчёт" },
  { value: "order", label: "Приказ" },
  { value: "application", label: "Заявление" },
  { value: "other", label: "Прочее" },
];

const CATEGORY_COLORS: Record<string, string> = {
  contract: "blue",
  act: "green",
  invoice: "gold",
  report: "purple",
  order: "red",
  application: "cyan",
  other: "default",
};

const categoryLabel = (cat: string) =>
  CATEGORIES.find((c) => c.value === cat)?.label ?? cat;

export const TemplatesPage = () => {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [form] = Form.useForm<CreateTemplateRequest & { id?: string }>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [fields, setFields] = useState<TemplateField[]>([]);
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["templates", search],
    queryFn: () => templatesApi.list({ search: search || undefined, active_only: false }),
  });

  const createMutation = useMutation({
    mutationFn: (d: CreateTemplateRequest) => templatesApi.create(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      message.success("Шаблон создан");
      closeModal();
    },
    onError: () => message.error("Ошибка при создании шаблона"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTemplateRequest }) =>
      templatesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      message.success("Шаблон обновлён");
      closeModal();
    },
    onError: () => message.error("Ошибка при обновлении шаблона"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => templatesApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      message.success("Шаблон удалён");
    },
    onError: () => message.error("Ошибка при удалении шаблона"),
  });

  const openCreate = () => {
    setEditingId(null);
    setFields([]);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (tpl: DocumentTemplate) => {
    setEditingId(tpl.id);
    setFields(tpl.fields as TemplateField[]);
    form.setFieldsValue({
      name: tpl.name,
      description: tpl.description,
      category: tpl.category,
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
    setFields([]);
    form.resetFields();
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    const payload = { ...values, fields };

    if (editingId) {
      updateMutation.mutate({ id: editingId, data: payload });
    } else {
      createMutation.mutate(payload as CreateTemplateRequest);
    }
  };

  const columns: ColumnsType<DocumentTemplate> = [
    {
      title: t("common.name"),
      dataIndex: "name",
      key: "name",
      render: (name, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{name}</Text>
          {record.description && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.description}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: "Категория",
      dataIndex: "category",
      key: "category",
      width: 150,
      render: (cat) => (
        <Tag color={CATEGORY_COLORS[cat] ?? "default"}>{categoryLabel(cat)}</Tag>
      ),
    },
    {
      title: "Полей",
      key: "fields_count",
      width: 80,
      align: "center",
      render: (_, record) => (
        <Tag>{(record.fields as TemplateField[]).length}</Tag>
      ),
    },
    {
      title: t("common.status"),
      dataIndex: "is_active",
      key: "is_active",
      width: 100,
      render: (active) => (
        <Tag color={active ? "green" : "red"}>{active ? "Активен" : "Архив"}</Tag>
      ),
    },
    {
      title: t("common.date"),
      dataIndex: "created_at",
      key: "created_at",
      width: 120,
      render: (d) => new Date(d).toLocaleDateString("ru-KZ"),
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: 100,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => openEdit(record)}
          />
          <Popconfirm
            title="Удалить шаблон?"
            description="Шаблон будет деактивирован."
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText={t("common.yes")}
            cancelText={t("common.no")}
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
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
          {t("nav.templates")}
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Создать шаблон
        </Button>
      </div>

      <Input.Search
        placeholder={t("common.search")}
        style={{ maxWidth: 400, marginBottom: 16 }}
        allowClear
        onSearch={setSearch}
        onChange={(e) => !e.target.value && setSearch("")}
      />

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        pagination={{
          total: data?.total,
          pageSize: data?.page_size ?? 20,
          showSizeChanger: false,
          showTotal: (total) => `Всего: ${total}`,
        }}
      />

      <Modal
        title={editingId ? "Редактировать шаблон" : "Создать шаблон"}
        open={modalOpen}
        onCancel={closeModal}
        onOk={handleSubmit}
        okText={editingId ? t("common.save") : t("common.create")}
        cancelText={t("common.cancel")}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="Название шаблона"
            rules={[{ required: true, message: "Введите название" }]}
          >
            <Input placeholder="Договор поставки товаров" maxLength={255} />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={2} maxLength={2000} />
          </Form.Item>

          <Form.Item
            name="category"
            label="Категория"
            rules={[{ required: true, message: "Выберите категорию" }]}
            initialValue="other"
          >
            <Select>
              {CATEGORIES.map((c) => (
                <Option key={c.value} value={c.value}>
                  {c.label}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="Поля шаблона">
            <TemplateFieldsEditor value={fields} onChange={setFields} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};
