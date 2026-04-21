import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Button,
  Card,
  Checkbox,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Select,
  Space,
  Spin,
  Typography,
  message,
} from "antd";
import { ArrowLeftOutlined, SaveOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { DocumentTemplate, TemplateField } from "@/types";
import { type CreateDocumentRequest, documentsApi, templatesApi } from "@/api/documents";

const { Title, Text } = Typography;
const { Option } = Select;

const DynamicField = ({
  field,
  onChange,
  value,
}: {
  field: TemplateField;
  value: unknown;
  onChange: (v: unknown) => void;
}) => {
  switch (field.type) {
    case "number":
      return (
        <InputNumber
          style={{ width: "100%" }}
          value={value as number}
          onChange={onChange}
          placeholder={field.label}
        />
      );
    case "date":
      return (
        <DatePicker
          style={{ width: "100%" }}
          format="DD.MM.YYYY"
          onChange={(_, str) => onChange(str)}
        />
      );
    case "select":
      return (
        <Select
          style={{ width: "100%" }}
          value={value as string}
          onChange={onChange}
          placeholder={`Выберите ${field.label.toLowerCase()}`}
        >
          {(field.options ?? []).map((opt) => (
            <Option key={opt} value={opt}>
              {opt}
            </Option>
          ))}
        </Select>
      );
    case "textarea":
      return (
        <Input.TextArea
          rows={3}
          value={value as string}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.label}
        />
      );
    case "checkbox":
      return (
        <Checkbox
          checked={!!value}
          onChange={(e) => onChange(e.target.checked)}
        >
          {field.label}
        </Checkbox>
      );
    default:
      return (
        <Input
          value={value as string}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.label}
        />
      );
  }
};

export const CreateDocumentPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [form] = Form.useForm();
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [fieldValues, setFieldValues] = useState<Record<string, unknown>>({});

  const { data: templates, isLoading: loadingTemplates } = useQuery({
    queryKey: ["templates-short"],
    queryFn: () => templatesApi.listShort(),
  });

  const selectedTemplate = templates?.find((t) => t.id === selectedTemplateId) as
    | DocumentTemplate
    | undefined;

  const fields = (selectedTemplate?.fields ?? []) as TemplateField[];

  // Сброс значений полей при смене шаблона
  useEffect(() => {
    const defaults: Record<string, unknown> = {};
    fields.forEach((f) => {
      defaults[f.name] = f.default_value ?? (f.type === "checkbox" ? false : "");
    });
    setFieldValues(defaults);
  }, [selectedTemplateId]);

  const createMutation = useMutation({
    mutationFn: (data: CreateDocumentRequest) => documentsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      message.success("Документ создан");
      navigate("/documents");
    },
    onError: () => message.error("Ошибка при создании документа"),
  });

  const handleSubmit = async () => {
    const values = await form.validateFields();

    // Проверяем обязательные поля шаблона
    const missingRequired = fields.filter(
      (f) => f.required && !fieldValues[f.name] && fieldValues[f.name] !== false
    );
    if (missingRequired.length > 0) {
      message.error(
        `Заполните обязательные поля: ${missingRequired.map((f) => f.label).join(", ")}`
      );
      return;
    }

    createMutation.mutate({
      title: values.title,
      template_id: selectedTemplateId ?? undefined,
      data: fieldValues,
      status: values.status ?? "draft",
    });
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <Button
          type="text"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate("/documents")}
        />
        <Title level={3} style={{ margin: 0 }}>
          {t("documents.create")}
        </Title>
      </div>

      <Card>
        <Form form={form} layout="vertical">
          {/* Название документа */}
          <Form.Item
            name="title"
            label="Название документа"
            rules={[{ required: true, message: "Введите название документа" }]}
          >
            <Input placeholder="Договор №123 с ТОО «Рога и Копыта»" maxLength={500} />
          </Form.Item>

          {/* Выбор шаблона */}
          <Form.Item name="template_id" label="Шаблон (необязательно)">
            {loadingTemplates ? (
              <Spin size="small" />
            ) : (
              <Select
                placeholder="Выберите шаблон..."
                allowClear
                showSearch
                optionFilterProp="children"
                onChange={(v) => setSelectedTemplateId(v ?? null)}
              >
                {(templates ?? []).map((tpl) => (
                  <Option key={tpl.id} value={tpl.id}>
                    {tpl.name}
                  </Option>
                ))}
              </Select>
            )}
          </Form.Item>

          {/* Статус */}
          <Form.Item name="status" label="Начальный статус" initialValue="draft">
            <Select style={{ width: 200 }}>
              <Option value="draft">Черновик</Option>
              <Option value="active">Активный</Option>
            </Select>
          </Form.Item>

          {/* Динамические поля шаблона */}
          {fields.length > 0 && (
            <Card
              title="Данные документа"
              size="small"
              style={{ marginTop: 8, marginBottom: 16 }}
            >
              {fields.map((field) => (
                <Form.Item
                  key={field.id}
                  label={
                    <Space>
                      <Text>{field.label}</Text>
                      {field.required && <Text type="danger">*</Text>}
                    </Space>
                  }
                  style={{ marginBottom: 16 }}
                >
                  <DynamicField
                    field={field}
                    value={fieldValues[field.name]}
                    onChange={(v) =>
                      setFieldValues((prev) => ({ ...prev, [field.name]: v }))
                    }
                  />
                </Form.Item>
              ))}
            </Card>
          )}
        </Form>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
          <Button onClick={() => navigate("/documents")}>{t("common.cancel")}</Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            loading={createMutation.isPending}
            onClick={handleSubmit}
          >
            Создать документ
          </Button>
        </div>
      </Card>
    </div>
  );
};
