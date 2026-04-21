import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  Button,
  Input,
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
  EyeOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { ColumnsType } from "antd/es/table";
import type { Document, DocumentStatus } from "@/types";
import { documentsApi } from "@/api/documents";

const { Title, Text } = Typography;
const { Option } = Select;

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  draft: { color: "default", label: "Черновик" },
  active: { color: "green", label: "Активный" },
  archived: { color: "blue", label: "Архив" },
  deleted: { color: "red", label: "Удалён" },
};

export const DocumentsPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["documents", page, search, statusFilter],
    queryFn: () =>
      documentsApi.list({
        page,
        search: search || undefined,
        status: statusFilter,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      message.success("Документ удалён");
    },
    onError: () => message.error("Ошибка при удалении документа"),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      documentsApi.updateStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      message.success("Статус обновлён");
    },
  });

  const columns: ColumnsType<Document> = [
    {
      title: "Название",
      dataIndex: "title",
      key: "title",
      render: (title) => <Text strong>{title}</Text>,
    },
    {
      title: t("common.status"),
      dataIndex: "status",
      key: "status",
      width: 130,
      render: (status: DocumentStatus) => {
        const cfg = STATUS_CONFIG[status] ?? { color: "default", label: status };
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      },
    },
    {
      title: t("common.date"),
      dataIndex: "created_at",
      key: "created_at",
      width: 130,
      render: (d) => new Date(d).toLocaleDateString("ru-KZ"),
    },
    {
      title: t("common.actions"),
      key: "actions",
      width: 160,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/documents/${record.id}`)}
          />
          {record.status === "draft" && (
            <Button
              type="text"
              size="small"
              onClick={() =>
                statusMutation.mutate({ id: record.id, status: "active" })
              }
            >
              Активировать
            </Button>
          )}
          {record.status === "active" && (
            <Button
              type="text"
              size="small"
              onClick={() =>
                statusMutation.mutate({ id: record.id, status: "archived" })
              }
            >
              В архив
            </Button>
          )}
          <Popconfirm
            title="Удалить документ?"
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
          {t("documents.title")}
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate("/documents/create")}
        >
          {t("documents.create")}
        </Button>
      </div>

      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder={t("common.search")}
          style={{ width: 320 }}
          allowClear
          onSearch={setSearch}
          onChange={(e) => !e.target.value && setSearch("")}
        />
        <Select
          placeholder="Все статусы"
          allowClear
          style={{ width: 160 }}
          onChange={(v) => { setStatusFilter(v); setPage(1); }}
        >
          <Option value="draft">Черновик</Option>
          <Option value="active">Активный</Option>
          <Option value="archived">Архив</Option>
        </Select>
      </Space>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        pagination={{
          current: page,
          total: data?.total,
          pageSize: data?.page_size ?? 20,
          showSizeChanger: false,
          showTotal: (total) => `Всего: ${total}`,
          onChange: setPage,
        }}
      />
    </div>
  );
};
