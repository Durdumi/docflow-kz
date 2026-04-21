import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Button,
  Card,
  Input,
  Popconfirm,
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
  EditOutlined,
  FileOutlined,
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentsApi } from "@/api/documents";

const { Title } = Typography;
const { Search } = Input;

const STATUS_OPTIONS = [
  { value: "",         label: "Все статусы" },
  { value: "draft",    label: "Черновик" },
  { value: "active",   label: "Активный" },
  { value: "archived", label: "Архив" },
];

const STATUS_COLOR: Record<string, string> = {
  draft:    "orange",
  active:   "green",
  archived: "default",
  deleted:  "red",
};

const STATUS_LABEL: Record<string, string> = {
  draft:    "Черновик",
  active:   "Активный",
  archived: "Архив",
  deleted:  "Удалён",
};

export const DocumentsPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["documents", page, search, statusFilter],
    queryFn: () =>
      documentsApi.list({
        page,
        page_size: 20,
        search: search || undefined,
        status: statusFilter || undefined,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      message.success("Документ удалён");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: () => message.error("Ошибка при удалении"),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      documentsApi.changeStatus(id, status),
    onSuccess: () => {
      message.success("Статус обновлён");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: () => message.error("Ошибка при смене статуса"),
  });

  const columns = [
    {
      title: "Название",
      dataIndex: "title",
      key: "title",
      ellipsis: true,
      render: (text: string) => (
        <Space>
          <FileOutlined style={{ color: "#1677ff" }} />
          {text}
        </Space>
      ),
    },
    {
      title: "Статус",
      dataIndex: "status",
      key: "status",
      width: 160,
      render: (status: string, record: { id: string }) => (
        <Select
          value={status}
          size="small"
          style={{ width: 140 }}
          loading={statusMutation.isPending}
          onChange={(val) => statusMutation.mutate({ id: record.id, status: val })}
          options={STATUS_OPTIONS.filter((o) => o.value).map((o) => ({
            value: o.value,
            label: <Tag color={STATUS_COLOR[o.value]}>{o.label}</Tag>,
          }))}
        />
      ),
    },
    {
      title: "Создан",
      dataIndex: "created_at",
      key: "created_at",
      width: 120,
      render: (d: string) => new Date(d).toLocaleDateString("ru-RU"),
    },
    {
      title: "Действия",
      key: "actions",
      width: 100,
      render: (_: unknown, record: { id: string }) => (
        <Space>
          <Tooltip title="Редактировать">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => navigate(`/documents/${record.id}/edit`)}
            />
          </Tooltip>
          <Tooltip title="Удалить">
            <Popconfirm
              title="Удалить документ?"
              onConfirm={() => deleteMutation.mutate(record.id)}
              okText="Да"
              cancelText="Нет"
            >
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Tooltip>
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
          marginBottom: 24,
        }}
      >
        <Title level={3} style={{ margin: 0 }}>
          Документы
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate("/documents/create")}
        >
          Создать документ
        </Button>
      </div>

      <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
        <Space style={{ marginBottom: 16 }}>
          <Search
            placeholder="Поиск по названию..."
            onSearch={(val) => { setSearch(val); setPage(1); }}
            onChange={(e) => { if (!e.target.value) { setSearch(""); setPage(1); } }}
            style={{ width: 280 }}
            prefix={<SearchOutlined />}
            allowClear
          />
          <Select
            value={statusFilter}
            onChange={(val) => { setStatusFilter(val); setPage(1); }}
            options={STATUS_OPTIONS}
            style={{ width: 160 }}
          />
        </Space>

        <Table
          dataSource={data?.items ?? []}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: 20,
            total: data?.total ?? 0,
            onChange: setPage,
            showTotal: (total) => `Всего: ${total}`,
          }}
          locale={{ emptyText: "Документов не найдено" }}
        />
      </Card>
    </div>
  );
};
