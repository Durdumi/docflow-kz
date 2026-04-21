import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  Card,
  Col,
  Form,
  Input,
  Row,
  Select,
  Space,
  Typography,
  message,
} from "antd";
import { ArrowLeftOutlined, SaveOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentsApi, templatesApi } from "@/api/documents";
import type { TemplateField, TemplateShort } from "@/api/documents";

const { Title } = Typography;
const { TextArea } = Input;

export const CreateDocumentPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateShort | null>(null);

  const { data: templates = [] } = useQuery({
    queryKey: ["templates-short"],
    queryFn: templatesApi.listShort,
  });

  const createMutation = useMutation({
    mutationFn: documentsApi.create,
    onSuccess: (doc: { id: string }) => {
      message.success("Документ создан");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      navigate("/documents");
    },
    onError: (err: { response?: { data?: { detail?: string } } }) => {
      message.error(err?.response?.data?.detail ?? "Ошибка при создании");
    },
  });

  const onTemplateSelect = (templateId: string) => {
    const tmpl = templates.find((t) => t.id === templateId) ?? null;
    setSelectedTemplate(tmpl);
    form.setFieldValue("template_id", templateId);
  };

  const onTemplateClear = () => {
    setSelectedTemplate(null);
    form.setFieldValue("template_id", undefined);
  };

  const onFinish = (values: Record<string, unknown>) => {
    const fieldData: Record<string, unknown> = {};
    if (selectedTemplate?.fields) {
      selectedTemplate.fields.forEach((field) => {
        fieldData[field.name] = values[`field_${field.name}`] ?? "";
      });
    } else if (values.content) {
      fieldData.content = values.content;
    }

    createMutation.mutate({
      title: values.title as string,
      template_id: (values.template_id as string) || null,
      data: fieldData,
      status: "draft",
    });
  };

  return (
    <div>
      <div
        style={{
          marginBottom: 24,
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate("/documents")}>
          Назад
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          Новый документ
        </Title>
      </div>

      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Row gutter={[24, 0]}>
          <Col xs={24} lg={16}>
            <Card
              bordered={false}
              style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)", marginBottom: 16 }}
            >
              <Form.Item
                name="title"
                label="Название документа"
                rules={[{ required: true, message: "Введите название" }]}
              >
                <Input
                  placeholder="Например: Договор №123 от 01.04.2026"
                  size="large"
                />
              </Form.Item>

              <Form.Item name="template_id" label="Шаблон (необязательно)">
                <Select
                  placeholder="Выбрать шаблон"
                  allowClear
                  onChange={onTemplateSelect}
                  onClear={onTemplateClear}
                  options={templates.map((t) => ({ value: t.id, label: t.name }))}
                />
              </Form.Item>

              {selectedTemplate?.fields?.map((field: TemplateField) => (
                <Form.Item
                  key={field.name}
                  name={`field_${field.name}`}
                  label={field.label}
                  rules={[
                    {
                      required: field.required,
                      message: `Заполните поле "${field.label}"`,
                    },
                  ]}
                >
                  {field.type === "textarea" ? (
                    <TextArea rows={3} placeholder={field.label} />
                  ) : field.type === "select" ? (
                    <Select
                      placeholder={field.label}
                      options={(field.options ?? []).map((o) => ({
                        value: o,
                        label: o,
                      }))}
                    />
                  ) : (
                    <Input
                      type={
                        field.type === "number"
                          ? "number"
                          : field.type === "date"
                          ? "date"
                          : "text"
                      }
                      placeholder={field.label}
                    />
                  )}
                </Form.Item>
              ))}

              {!selectedTemplate && (
                <Form.Item name="content" label="Содержание (свободный текст)">
                  <TextArea rows={6} placeholder="Введите текст документа..." />
                </Form.Item>
              )}
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
              <Title level={5}>Действия</Title>
              <Space direction="vertical" style={{ width: "100%" }}>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  htmlType="submit"
                  loading={createMutation.isPending}
                  block
                >
                  Сохранить как черновик
                </Button>
                <Button block onClick={() => navigate("/documents")}>
                  Отмена
                </Button>
              </Space>

              {selectedTemplate && (
                <div style={{ marginTop: 16, fontSize: 12, color: "#8c8c8c" }}>
                  Шаблон: <strong>{selectedTemplate.name}</strong>
                  <br />
                  Полей: {selectedTemplate.fields?.length ?? 0}
                </div>
              )}
            </Card>
          </Col>
        </Row>
      </Form>
    </div>
  );
};
