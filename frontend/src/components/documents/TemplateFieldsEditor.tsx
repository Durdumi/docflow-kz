import { Button, Checkbox, Input, Select, Space, Table, Tag } from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import type { TemplateField } from "@/types";

const { Option } = Select;

const FIELD_TYPES = [
  { value: "text", label: "Текст" },
  { value: "number", label: "Число" },
  { value: "date", label: "Дата" },
  { value: "select", label: "Выбор" },
  { value: "textarea", label: "Текст (многострочный)" },
  { value: "checkbox", label: "Флажок" },
];

interface Props {
  value: TemplateField[];
  onChange: (fields: TemplateField[]) => void;
}

export const TemplateFieldsEditor = ({ value, onChange }: Props) => {
  const addField = () => {
    const newField: TemplateField = {
      id: `field_${Date.now()}`,
      name: `field_${value.length + 1}`,
      label: `Поле ${value.length + 1}`,
      type: "text",
      required: false,
    };
    onChange([...value, newField]);
  };

  const updateField = (index: number, patch: Partial<TemplateField>) => {
    const updated = value.map((f, i) => (i === index ? { ...f, ...patch } : f));
    onChange(updated);
  };

  const removeField = (index: number) => {
    onChange(value.filter((_, i) => i !== index));
  };

  const columns: ColumnsType<TemplateField & { _index: number }> = [
    {
      title: "ID / name",
      key: "name",
      width: 160,
      render: (_, row) => (
        <Input
          size="small"
          value={row.name}
          onChange={(e) => updateField(row._index, { name: e.target.value, id: e.target.value })}
          placeholder="field_name"
        />
      ),
    },
    {
      title: "Метка",
      key: "label",
      render: (_, row) => (
        <Input
          size="small"
          value={row.label}
          onChange={(e) => updateField(row._index, { label: e.target.value })}
          placeholder="Название поля"
        />
      ),
    },
    {
      title: "Тип",
      key: "type",
      width: 160,
      render: (_, row) => (
        <Select
          size="small"
          value={row.type}
          style={{ width: "100%" }}
          onChange={(v) => updateField(row._index, { type: v as TemplateField["type"] })}
        >
          {FIELD_TYPES.map((t) => (
            <Option key={t.value} value={t.value}>
              {t.label}
            </Option>
          ))}
        </Select>
      ),
    },
    {
      title: "Обяз.",
      key: "required",
      width: 60,
      align: "center",
      render: (_, row) => (
        <Checkbox
          checked={row.required}
          onChange={(e) => updateField(row._index, { required: e.target.checked })}
        />
      ),
    },
    {
      key: "actions",
      width: 40,
      render: (_, row) => (
        <Button
          type="text"
          danger
          size="small"
          icon={<DeleteOutlined />}
          onClick={() => removeField(row._index)}
        />
      ),
    },
  ];

  const dataSource = value.map((f, i) => ({ ...f, _index: i, key: f.id || i }));

  return (
    <Space direction="vertical" style={{ width: "100%" }}>
      {value.length === 0 ? (
        <Tag color="default" style={{ padding: "4px 8px" }}>
          Нет полей — шаблон будет свободного формата
        </Tag>
      ) : (
        <Table
          size="small"
          columns={columns}
          dataSource={dataSource}
          pagination={false}
          bordered
        />
      )}
      <Button
        type="dashed"
        icon={<PlusOutlined />}
        onClick={addField}
        style={{ width: "100%" }}
      >
        Добавить поле
      </Button>
    </Space>
  );
};
