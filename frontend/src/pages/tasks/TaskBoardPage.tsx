import { useState } from "react";
import {
  Badge, Button, Card, DatePicker, Form,
  Input, Modal, Popconfirm, Select, Space, Tag,
  Tooltip, Typography, message,
} from "antd";
import {
  CalendarOutlined, DeleteOutlined, PlusOutlined,
} from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tasksApi } from "@/api/tasks";
import dayjs from "dayjs";

const { Title, Text } = Typography;
const { TextArea } = Input;

const COLUMNS = [
  { key: "todo",        label: "📋 Надо сделать", color: "#f0f0f0" },
  { key: "in_progress", label: "⚡ В работе",      color: "#e6f4ff" },
  { key: "review",      label: "👀 На проверке",   color: "#fff7e6" },
  { key: "done",        label: "✅ Готово",         color: "#f6ffed" },
];

const PRIORITY_CONFIG: Record<string, { color: string; label: string; icon: string }> = {
  low:    { color: "default", label: "Низкий",  icon: "↓" },
  medium: { color: "blue",    label: "Средний", icon: "→" },
  high:   { color: "orange",  label: "Высокий", icon: "↑" },
  urgent: { color: "red",     label: "Срочно",  icon: "🔥" },
};

const PRIORITY_OPTIONS = [
  { value: "low",    label: "↓ Низкий" },
  { value: "medium", label: "→ Средний" },
  { value: "high",   label: "↑ Высокий" },
  { value: "urgent", label: "🔥 Срочно" },
];

const STATUS_OPTIONS = [
  { value: "todo",        label: "📋 Надо сделать" },
  { value: "in_progress", label: "⚡ В работе" },
  { value: "review",      label: "👀 На проверке" },
  { value: "done",        label: "✅ Готово" },
];

export const TaskBoardPage = () => {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [editTask, setEditTask] = useState<any>(null);
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: tasksApi.create,
    onSuccess: () => {
      message.success("Задача создана");
      setCreateOpen(false);
      createForm.resetFields();
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
    onError: (err: any) => message.error(err?.response?.data?.detail || "Ошибка"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => tasksApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      if (editTask) {
        setEditTask(null);
        message.success("Задача обновлена");
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: tasksApi.delete,
    onSuccess: () => {
      message.success("Задача удалена");
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const onCreateFinish = (values: any) => {
    createMutation.mutate({
      ...values,
      due_date: values.due_date?.toISOString() ?? null,
    });
  };

  const onEditFinish = (values: any) => {
    if (!editTask) return;
    updateMutation.mutate({
      id: editTask.id,
      data: { ...values, due_date: values.due_date?.toISOString() ?? null },
    });
  };

  const moveTask = (task: any, newStatus: string) => {
    updateMutation.mutate({ id: task.id, data: { status: newStatus } });
  };

  const isOverdue = (task: any) =>
    task.due_date && new Date(task.due_date) < new Date() && task.status !== "done";

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Таскборд</Title>
          <Text type="secondary">Управление задачами организации</Text>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
          Новая задача
        </Button>
      </div>

      {/* Kanban Board */}
      <div style={{ display: "flex", gap: 16, overflowX: "auto", paddingBottom: 16 }}>
        {COLUMNS.map((col) => {
          const colTasks = tasks.filter((t: any) => t.status === col.key);
          return (
            <div key={col.key} style={{ minWidth: 280, width: 280, flexShrink: 0 }}>
              <div
                style={{
                  background: col.color,
                  borderRadius: 12,
                  padding: 12,
                  minHeight: 400,
                }}
              >
                <div style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 12,
                }}>
                  <Text strong>{col.label}</Text>
                  <Badge count={colTasks.length} color="#1677ff" />
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {colTasks.map((task: any) => {
                    const priority = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;
                    const overdue = isOverdue(task);

                    return (
                      <Card
                        key={task.id}
                        size="small"
                        style={{
                          borderRadius: 8,
                          border: overdue ? "1px solid #ff4d4f" : "1px solid #f0f0f0",
                          cursor: "pointer",
                          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                        }}
                        onClick={() => {
                          setEditTask(task);
                          editForm.setFieldsValue({
                            ...task,
                            due_date: task.due_date ? dayjs(task.due_date) : null,
                          });
                        }}
                      >
                        <div style={{ marginBottom: 8 }}>
                          <Text strong style={{ fontSize: 13 }}>{task.title}</Text>
                          {overdue && (
                            <Tag color="red" style={{ marginLeft: 6, fontSize: 10 }}>
                              Просрочено
                            </Tag>
                          )}
                        </div>

                        {task.description && (
                          <Text
                            type="secondary"
                            style={{ fontSize: 11, display: "block", marginBottom: 8 }}
                          >
                            {task.description.slice(0, 60)}
                            {task.description.length > 60 ? "..." : ""}
                          </Text>
                        )}

                        <div style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                        }}>
                          <Tag color={priority.color} style={{ fontSize: 10 }}>
                            {priority.icon} {priority.label}
                          </Tag>
                          {task.due_date && (
                            <Tooltip title={dayjs(task.due_date).format("DD.MM.YYYY")}>
                              <Text
                                type={overdue ? "danger" : "secondary"}
                                style={{ fontSize: 10 }}
                              >
                                <CalendarOutlined /> {dayjs(task.due_date).format("DD.MM.YYYY")}
                              </Text>
                            </Tooltip>
                          )}
                        </div>

                        <div
                          style={{ marginTop: 8, display: "flex", gap: 4 }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          {COLUMNS.filter(c => c.key !== col.key).map(c => (
                            <Tooltip key={c.key} title={`→ ${c.label}`}>
                              <Button
                                size="small"
                                style={{ fontSize: 10, padding: "0 6px", height: 20 }}
                                onClick={() => moveTask(task, c.key)}
                              >
                                {c.label.split(" ")[0]}
                              </Button>
                            </Tooltip>
                          ))}
                          <Popconfirm
                            title="Удалить задачу?"
                            onConfirm={() => deleteMutation.mutate(task.id)}
                            okText="Да"
                            cancelText="Нет"
                          >
                            <Button
                              size="small"
                              danger
                              icon={<DeleteOutlined />}
                              style={{ height: 20, padding: "0 4px", fontSize: 10 }}
                            />
                          </Popconfirm>
                        </div>
                      </Card>
                    );
                  })}

                  <Button
                    type="dashed"
                    block
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={() => {
                      createForm.setFieldValue("status", col.key);
                      setCreateOpen(true);
                    }}
                    style={{ marginTop: 4 }}
                  >
                    Добавить
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Create Modal */}
      <Modal
        title="Новая задача"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); createForm.resetFields(); }}
        onOk={() => createForm.submit()}
        confirmLoading={createMutation.isPending}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={createForm} layout="vertical" onFinish={onCreateFinish} style={{ marginTop: 16 }}>
          <Form.Item name="title" label="Название" rules={[{ required: true, message: "Введите название" }]}>
            <Input placeholder="Что нужно сделать?" />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <TextArea rows={2} placeholder="Подробности..." />
          </Form.Item>
          <div style={{ display: "flex", gap: 12 }}>
            <Form.Item name="priority" label="Приоритет" initialValue="medium" style={{ flex: 1 }}>
              <Select options={PRIORITY_OPTIONS} />
            </Form.Item>
            <Form.Item name="status" label="Колонка" initialValue="todo" style={{ flex: 1 }}>
              <Select options={STATUS_OPTIONS} />
            </Form.Item>
          </div>
          <Form.Item name="due_date" label="Дедлайн">
            <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        title="Редактировать задачу"
        open={!!editTask}
        onCancel={() => { setEditTask(null); editForm.resetFields(); }}
        onOk={() => editForm.submit()}
        confirmLoading={updateMutation.isPending}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={editForm} layout="vertical" onFinish={onEditFinish} style={{ marginTop: 16 }}>
          <Form.Item name="title" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <TextArea rows={3} />
          </Form.Item>
          <div style={{ display: "flex", gap: 12 }}>
            <Form.Item name="priority" label="Приоритет" style={{ flex: 1 }}>
              <Select options={PRIORITY_OPTIONS} />
            </Form.Item>
            <Form.Item name="status" label="Статус" style={{ flex: 1 }}>
              <Select options={STATUS_OPTIONS} />
            </Form.Item>
          </div>
          <Form.Item name="due_date" label="Дедлайн">
            <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TaskBoardPage;
