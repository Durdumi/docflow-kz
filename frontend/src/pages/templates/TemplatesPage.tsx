import { useState } from "react";
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  Modal,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { DeleteOutlined, EditOutlined, PlusOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { templatesApi } from "@/api/documents";
import type { TemplateField } from "@/api/documents";

const { Title, Text } = Typography;
const { TextArea } = Input;

const FIELD_TYPES = [
  { value: "text",     label: "Текст" },
  { value: "number",   label: "Число" },
  { value: "date",     label: "Дата" },
  { value: "textarea", label: "Большой текст" },
  { value: "select",   label: "Список" },
  { value: "checkbox", label: "Флажок" },
];

// Значения соответствуют TemplateCategory enum на бэкенде
const CATEGORY_OPTIONS = [
  { value: "contract",    label: "Договор" },
  { value: "act",         label: "Акт" },
  { value: "invoice",     label: "Счёт / Накладная" },
  { value: "report",      label: "Отчёт" },
  { value: "order",       label: "Приказ" },
  { value: "application", label: "Заявление" },
  { value: "other",       label: "Прочее" },
];

const CATEGORY_LABEL: Record<string, string> = Object.fromEntries(
  CATEGORY_OPTIONS.map((o) => [o.value, o.label])
);

interface FieldRow {
  _key: string; // UI-only key
  id: string;
  name: string;
  label: string;
  type: TemplateField["type"];
  required: boolean;
  options?: string[];
}

const makeField = (): FieldRow => {
  const uid = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
  return {
    _key: uid,
    id: uid,
    name: `field_${uid}`,
    label: "",
    type: "text",
    required: false,
  };
};

const slugify = (s: string) =>
  s
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_а-яё]/gi, "")
    .slice(0, 80) || `field_${Date.now().toString(36)}`;

export const TemplatesPage = () => {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [fields, setFields] = useState<FieldRow[]>([]);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ["templates"],
    queryFn: () => templatesApi.list({ page: 1, page_size: 100 }),
  });

  const templates = data?.items ?? [];

  const saveMutation = useMutation({
    mutationFn: (values: { name: string; description?: string; category: string }) => {
      const payload = {
        ...values,
        fields: fields.map(({ _key, ...f }) => f) as TemplateField[],
      };
      return editingId
        ? templatesApi.update(editingId, payload)
        : templatesApi.create(payload);
    },
    onSuccess: () => {
      message.success(editingId ? "Шаблон обновлён" : "Шаблон создан");
      closeModal();
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      queryClient.invalidateQueries({ queryKey: ["templates-short"] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      message.error(err?.response?.data?.detail ?? "Ошибка при сохранении"),
  });

  const deleteMutation = useMutation({
    mutationFn: templatesApi.delete,
    onSuccess: () => {
      message.success("Шаблон удалён");
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      queryClient.invalidateQueries({ queryKey: ["templates-short"] });
    },
    onError: () => message.error("Ошибка при удалении"),
  });

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
    setFields([]);
    form.resetFields();
  };

  const openCreate = () => {
    closeModal();
    setModalOpen(true);
  };

  const openEdit = (tmpl: {
    id: string;
    name: string;
    description?: string;
    category: string;
    fields: TemplateField[];
  }) => {
    setEditingId(tmpl.id);
    setFields(
      (tmpl.fields ?? []).map((f) => ({
        _key: f.id,
        id: f.id,
        name: f.name,
        label: f.label,
        type: f.type as TemplateField["type"],
        required: f.required,
        options: f.options,
      }))
    );
    form.setFieldsValue({
      name: tmpl.name,
      description: tmpl.description,
      category: tmpl.category,
    });
    setModalOpen(true);
  };

  const addField = () => setFields((prev) => [...prev, makeField()]);

  const updateField = <K extends keyof FieldRow>(idx: number, key: K, val: FieldRow[K]) => {
    setFields((prev) =>
      prev.map((f, i) => {
        if (i !== idx) return f;
        const updated = { ...f, [key]: val };
        // автогенерация name из label
        if (key === "label" && typeof val === "string") {
          updated.name = slugify(val);
        }
        return updated;
      })
    );
  };

  const removeField = (idx: number) =>
    setFields((prev) => prev.filter((_, i) => i !== idx));

  const columns = [
    {
      title: "Название",
      dataIndex: "name",
      key: "name",
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: "Категория",
      dataIndex: "category",
      key: "category",
      width: 150,
      render: (cat: string) =>
        cat ? <Tag>{CATEGORY_LABEL[cat] ?? cat}</Tag> : "—",
    },
    {
      title: "Полей",
      dataIndex: "fields",
      key: "fields",
      width: 80,
      render: (f: unknown[]) => f?.length ?? 0,
    },
    {
      title: "Описание",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
      render: (d: string) => d || "—",
    },
    {
      title: "Действия",
      key: "actions",
      width: 140,
      render: (_: unknown, record: {
        id: string;
        name: string;
        description?: string;
        category: string;
        fields: TemplateField[];
      }) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            Изменить
          </Button>
          <Popconfirm
            title="Удалить шаблон?"
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

  return (
    <div>
      <div
        style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}
      >
        <Title level={3} style={{ margin: 0 }}>
          Шаблоны документов
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          Создать шаблон
        </Button>
      </div>

      <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
        <Table
          dataSource={templates}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          locale={{ emptyText: "Шаблонов пока нет. Создайте первый!" }}
        />
      </Card>

      <Modal
        title={editingId ? "Редактировать шаблон" : "Новый шаблон"}
        open={modalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={saveMutation.isPending}
        okText="Сохранить"
        cancelText="Отмена"
        width={700}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveMutation.mutate}
          style={{ marginTop: 16 }}
        >
          <Row gutter={12}>
            <Col span={16}>
              <Form.Item
                name="name"
                label="Название шаблона"
                rules={[{ required: true, message: "Введите название" }]}
              >
                <Input placeholder="Например: Трудовой договор" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="category"
                label="Категория"
                initialValue="other"
              >
                <Select options={CATEGORY_OPTIONS} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="Описание">
            <TextArea rows={2} placeholder="Краткое описание шаблона" />
          </Form.Item>

          <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 12 }}>
            <Text strong>Поля шаблона</Text>
            <Button size="small" icon={<PlusOutlined />} onClick={addField}>
              Добавить поле
            </Button>
          </div>

          {fields.length === 0 && (
            <Text type="secondary" style={{ fontSize: 13 }}>
              Нет полей — документ будет без структурированных данных.
            </Text>
          )}

          {fields.map((field, idx) => (
            <Card
              key={field._key}
              size="small"
              style={{ marginBottom: 8, background: "#fafafa" }}
              extra={
                <Button
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeField(idx)}
                />
              }
            >
              <Row gutter={8}>
                <Col span={10}>
                  <Input
                    placeholder="Заголовок поля (Label)"
                    value={field.label}
                    onChange={(e) => updateField(idx, "label", e.target.value)}
                    size="small"
                  />
                  <div style={{ fontSize: 11, color: "#aaa", marginTop: 2 }}>
                    key: {field.name}
                  </div>
                </Col>
                <Col span={8}>
                  <Select
                    value={field.type}
                    onChange={(val) => updateField(idx, "type", val)}
                    options={FIELD_TYPES}
                    size="small"
                    style={{ width: "100%" }}
                  />
                </Col>
                <Col span={6}>
                  <Select
                    value={field.required ? "required" : "optional"}
                    onChange={(val) =>
                      updateField(idx, "required", val === "required")
                    }
                    size="small"
                    style={{ width: "100%" }}
                    options={[
                      { value: "optional", label: "Необяз." },
                      { value: "required", label: "Обязат." },
                    ]}
                  />
                </Col>
              </Row>
            </Card>
          ))}
        </Form>
      </Modal>
    </div>
  );
};
