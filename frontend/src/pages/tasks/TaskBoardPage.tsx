import { useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  useDroppable,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import {
  Avatar, Badge, Button, Card, Checkbox, DatePicker, Divider,
  Form, Input, Modal, Popconfirm, Progress, Select, Space, Spin, Switch,
  Tabs, Tag, Timeline, Tooltip, Typography, message,
} from "antd";
import {
  CalendarOutlined, CheckSquareOutlined, DeleteOutlined, HolderOutlined,
  PlusOutlined, SettingOutlined, TeamOutlined,
} from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tasksApi, boardApi, activityApi } from "@/api/tasks";
import { boardsApi } from "@/api/boards";
import { usersApi } from "@/api/users";
import { useAuthStore } from "@/store/authStore";
import dayjs from "dayjs";

const { Title, Text } = Typography;
const { TextArea } = Input;

const PRIORITY_CONFIG: Record<string, { color: string; label: string; icon: string }> = {
  low:    { color: "default", label: "Низкий",  icon: "↓" },
  medium: { color: "blue",   label: "Средний",  icon: "→" },
  high:   { color: "orange", label: "Высокий",  icon: "↑" },
  urgent: { color: "red",    label: "Срочно",   icon: "🔥" },
};

const PRIORITY_OPTIONS = [
  { value: "low",    label: "↓ Низкий" },
  { value: "medium", label: "→ Средний" },
  { value: "high",   label: "↑ Высокий" },
  { value: "urgent", label: "🔥 Срочно" },
];

const COVER_COLORS = [
  "#ff7875", "#ffc069", "#ffd666", "#95de64",
  "#5cdbd3", "#69b1ff", "#b37feb", "#ff85c2",
];

// ─── Board Selector ───────────────────────────────────────────
function BoardSelector({
  boards,
  selectedId,
  onSelect,
  onManage,
}: {
  boards: any[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onManage: () => void;
}) {
  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      {boards.map((b: any) => (
        <Button
          key={b.id}
          type={selectedId === b.id ? "primary" : "default"}
          size="small"
          style={{ borderColor: b.color, color: selectedId === b.id ? "#fff" : b.color }}
          onClick={() => onSelect(b.id)}
        >
          {b.name}
        </Button>
      ))}
      <Tooltip title="Управление досками">
        <Button size="small" icon={<SettingOutlined />} onClick={onManage} />
      </Tooltip>
    </div>
  );
}

// ─── Boards Management Modal ──────────────────────────────────
function BoardsManageModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [addForm] = Form.useForm();
  const { data: boards = [] } = useQuery({ queryKey: ["boards"], queryFn: boardsApi.list });

  const createMut = useMutation({
    mutationFn: boardsApi.create,
    onSuccess: () => { message.success("Доска создана"); queryClient.invalidateQueries({ queryKey: ["boards"] }); addForm.resetFields(); },
    onError: () => message.error("Ошибка"),
  });
  const deleteMut = useMutation({
    mutationFn: boardsApi.remove,
    onSuccess: () => { message.success("Доска архивирована"); queryClient.invalidateQueries({ queryKey: ["boards"] }); },
  });

  return (
    <Modal title="Доски" open={open} onCancel={onClose} footer={null} width={500}>
      <div style={{ marginBottom: 16 }}>
        {(boards as any[]).map((b: any) => (
          <div key={b.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
            <div style={{ width: 14, height: 14, borderRadius: 3, background: b.color, flexShrink: 0 }} />
            <Text style={{ flex: 1 }}>{b.name}</Text>
            {b.description && <Text type="secondary" style={{ fontSize: 11 }}>{b.description}</Text>}
            <Popconfirm title="Архивировать доску?" onConfirm={() => deleteMut.mutate(b.id)} okText="Да" cancelText="Нет">
              <Button size="small" danger loading={deleteMut.isPending}>Архив</Button>
            </Popconfirm>
          </div>
        ))}
      </div>
      <Divider>Создать доску</Divider>
      <Form
        form={addForm}
        layout="inline"
        onFinish={(v) => createMut.mutate({ name: v.name, description: v.description, color: v.color || "#1677ff" })}
      >
        <Form.Item name="color" initialValue="#1677ff">
          <Input type="color" style={{ width: 40, padding: 2 }} />
        </Form.Item>
        <Form.Item name="name" rules={[{ required: true, message: "" }]}>
          <Input placeholder="Название доски" style={{ width: 200 }} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={createMut.isPending} icon={<PlusOutlined />}>
          Создать
        </Button>
      </Form>
    </Modal>
  );
}

// ─── Board Settings components ────────────────────────────────
function BoardColumnsSettings({ columns, onRefresh }: { columns: any[]; onRefresh: () => void }) {
  const [addForm] = Form.useForm();

  const addMutation = useMutation({
    mutationFn: boardApi.createColumn,
    onSuccess: () => { message.success("Колонка добавлена"); onRefresh(); addForm.resetFields(); },
    onError: () => message.error("Ошибка при добавлении"),
  });

  const deleteMutation = useMutation({
    mutationFn: boardApi.deleteColumn,
    onSuccess: () => { message.success("Колонка скрыта"); onRefresh(); },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => boardApi.updateColumn(id, data),
    onSuccess: () => { message.success("Сохранено"); onRefresh(); },
    onError: () => message.error("Ошибка сохранения"),
  });

  return (
    <div>
      <Text type="secondary" style={{ display: "block", marginBottom: 12 }}>
        Управляйте колонками доски. Переключатель «Финиш» — задачи в этой колонке считаются выполненными.
      </Text>
      {columns.map((col: any) => (
        <div key={col.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
          <div style={{ width: 16, height: 16, borderRadius: 4, background: col.color, border: "1px solid #e8e8e8", flexShrink: 0 }} />
          <Text style={{ flex: 1 }}>{col.label}</Text>
          <Tooltip title="Колонка «Готово»">
            <Switch
              size="small"
              checked={col.is_done_column}
              loading={updateMutation.isPending}
              onChange={(checked) => updateMutation.mutate({ id: col.id, data: { is_done_column: checked } })}
            />
          </Tooltip>
          <Text type="secondary" style={{ fontSize: 11, width: 40 }}>финиш</Text>
          <Popconfirm title="Скрыть колонку?" onConfirm={() => deleteMutation.mutate(col.id)} okText="Да" cancelText="Нет">
            <Button size="small" danger loading={deleteMutation.isPending}>Скрыть</Button>
          </Popconfirm>
        </div>
      ))}
      <Divider>Добавить колонку</Divider>
      <Form
        form={addForm}
        layout="inline"
        onFinish={(v) => addMutation.mutate({
          key: v.label.toLowerCase().replace(/\s+/g, "_").replace(/[^\w]/g, ""),
          label: v.label,
          color: v.color || "#f5f5f5",
          position: columns.length,
        })}
      >
        <Form.Item name="label" rules={[{ required: true, message: "" }]}>
          <Input placeholder="Название колонки" style={{ width: 180 }} />
        </Form.Item>
        <Form.Item name="color">
          <Input type="color" style={{ width: 40, padding: 2 }} defaultValue="#f5f5f5" />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={addMutation.isPending}>Добавить</Button>
      </Form>
    </div>
  );
}

function BoardLabelsSettings({ labels, onRefresh }: { labels: any[]; onRefresh: () => void }) {
  const [addForm] = Form.useForm();

  const addMutation = useMutation({
    mutationFn: boardApi.createLabel,
    onSuccess: () => { message.success("Метка добавлена"); onRefresh(); addForm.resetFields(); },
    onError: () => message.error("Ошибка при добавлении"),
  });

  const deleteMutation = useMutation({
    mutationFn: boardApi.deleteLabel,
    onSuccess: () => { message.success("Метка удалена"); onRefresh(); },
  });

  return (
    <div>
      {labels.map((label: any) => (
        <div key={label.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 0", borderBottom: "1px solid #f0f0f0" }}>
          <div style={{ width: 20, height: 20, borderRadius: "50%", background: label.color, border: "1px solid #e8e8e8", flexShrink: 0 }} />
          <Text style={{ flex: 1 }}>{label.name}</Text>
          <Tag color={label.color} style={{ fontSize: 11 }}>пример</Tag>
          <Popconfirm title="Удалить метку?" onConfirm={() => deleteMutation.mutate(label.id)} okText="Да" cancelText="Нет">
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </div>
      ))}
      <Divider>Добавить метку</Divider>
      <Form form={addForm} layout="inline" onFinish={(v) => addMutation.mutate(v)}>
        <Form.Item name="color" rules={[{ required: true, message: "" }]}>
          <Input type="color" style={{ width: 40, padding: 2 }} defaultValue="#1677ff" />
        </Form.Item>
        <Form.Item name="name" rules={[{ required: true, message: "" }]}>
          <Input placeholder="Название метки" style={{ width: 220 }} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={addMutation.isPending} icon={<PlusOutlined />}>Добавить</Button>
      </Form>
    </div>
  );
}

// ─── Checklist component ──────────────────────────────────────
function ChecklistEditor({
  items,
  onChange,
}: {
  items: Array<{ text: string; done: boolean }>;
  onChange: (items: Array<{ text: string; done: boolean }>) => void;
}) {
  const [newText, setNewText] = useState("");

  const toggle = (i: number) => {
    const next = items.map((item, idx) => idx === i ? { ...item, done: !item.done } : item);
    onChange(next);
  };

  const remove = (i: number) => {
    onChange(items.filter((_, idx) => idx !== i));
  };

  const add = () => {
    const text = newText.trim();
    if (!text) return;
    onChange([...items, { text, done: false }]);
    setNewText("");
  };

  const doneCount = items.filter((i) => i.done).length;
  const pct = items.length ? Math.round((doneCount / items.length) * 100) : 0;

  return (
    <div>
      {items.length > 0 && (
        <Progress percent={pct} size="small" style={{ marginBottom: 8 }} />
      )}
      {items.map((item, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
          <Checkbox checked={item.done} onChange={() => toggle(i)} />
          <Text style={{ flex: 1, textDecoration: item.done ? "line-through" : "none", color: item.done ? "#999" : undefined, fontSize: 13 }}>
            {item.text}
          </Text>
          <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={() => remove(i)} />
        </div>
      ))}
      <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
        <Input
          size="small"
          placeholder="Добавить пункт..."
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          onPressEnter={add}
          style={{ flex: 1 }}
        />
        <Button size="small" type="primary" icon={<PlusOutlined />} onClick={add}>Добавить</Button>
      </div>
    </div>
  );
}

// ─── Sortable Task Card ────────────────────────────────────────
function TaskCard({
  task, users, labels, doneColumnKey, onEdit, onDelete, onToggleDone, isDragging = false,
}: {
  task: any; users: any[]; labels: any[]; doneColumnKey: string | null;
  onEdit: (task: any) => void; onDelete: (id: string) => void;
  onToggleDone: (task: any) => void; isDragging?: boolean;
}) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: task.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  };

  const isDone = doneColumnKey ? task.status === doneColumnKey : task.status === "done";
  const priority = PRIORITY_CONFIG[task.priority] || PRIORITY_CONFIG.medium;
  const isOverdue = task.due_date && new Date(task.due_date) < new Date() && !isDone;
  const assignee = users.find((u: any) => u.id === task.assignee_id);
  const labelInfo = task.label_color ? labels.find((l: any) => l.color === task.label_color) : null;
  const checklist: Array<{ text: string; done: boolean }> = Array.isArray(task.checklist) ? task.checklist : [];
  const checkDone = checklist.filter((c) => c.done).length;

  return (
    <div ref={setNodeRef} style={style}>
      <Card
        size="small"
        style={{
          borderRadius: 8,
          border: isOverdue ? "1px solid #ff4d4f" : "1px solid #e8e8e8",
          boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
          marginBottom: 8,
          userSelect: "none",
          opacity: isDone ? 0.75 : 1,
          overflow: "hidden",
        }}
        styles={{ body: { padding: 0 } }}
      >
        {task.cover_color && (
          <div style={{ height: 6, background: task.cover_color, borderRadius: "8px 8px 0 0" }} />
        )}
        <div style={{ padding: "8px 10px" }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
            <Checkbox
              checked={isDone}
              onChange={(e) => { e.nativeEvent.stopImmediatePropagation(); onToggleDone(task); }}
              onClick={(e) => e.stopPropagation()}
              style={{ paddingTop: 2, flexShrink: 0 }}
            />
            <span
              {...attributes}
              {...listeners}
              style={{ color: "#bbb", cursor: "grab", paddingTop: 2, flexShrink: 0 }}
            >
              <HolderOutlined />
            </span>
            <div style={{ flex: 1, cursor: "pointer" }} onClick={() => onEdit(task)}>
              <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap" }}>
                {task.label_color && (
                  <Tooltip title={labelInfo?.name || ""}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: task.label_color, flexShrink: 0 }} />
                  </Tooltip>
                )}
                <Text strong style={{ fontSize: 13, textDecoration: isDone ? "line-through" : "none", color: isDone ? "#999" : undefined }}>
                  {task.title}
                </Text>
                {isOverdue && <Tag color="red" style={{ fontSize: 10, margin: 0 }}>Просрочено</Tag>}
              </div>
              {task.description && (
                <Text type="secondary" style={{ fontSize: 11, display: "block", marginTop: 2 }}>
                  {task.description.slice(0, 70)}{task.description.length > 70 ? "..." : ""}
                </Text>
              )}
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 6 }}>
            <Space size={4}>
              <Tag color={priority.color} style={{ fontSize: 10, margin: 0 }}>
                {priority.icon} {priority.label}
              </Tag>
              {checklist.length > 0 && (
                <Tag icon={<CheckSquareOutlined />} style={{ fontSize: 10, margin: 0 }}>
                  {checkDone}/{checklist.length}
                </Tag>
              )}
              {Array.isArray(task.assignee_ids) && task.assignee_ids.length > 1 && (
                <Tag icon={<TeamOutlined />} style={{ fontSize: 10, margin: 0 }}>
                  {task.assignee_ids.length}
                </Tag>
              )}
            </Space>
            <Space size={4}>
              {task.due_date && (
                <Text type={isOverdue ? "danger" : "secondary"} style={{ fontSize: 10 }}>
                  <CalendarOutlined /> {dayjs(task.due_date).format("DD.MM")}
                </Text>
              )}
              {assignee && (
                <Tooltip title={`${assignee.last_name} ${assignee.first_name}`}>
                  <Avatar size={18} style={{ backgroundColor: "#1677ff", fontSize: 10 }}>
                    {assignee.first_name?.[0]}{assignee.last_name?.[0]}
                  </Avatar>
                </Tooltip>
              )}
              <Popconfirm
                title="Удалить задачу?"
                onConfirm={() => onDelete(task.id)}
                okText="Да"
                cancelText="Нет"
              >
                <Button
                  size="small" danger type="text" icon={<DeleteOutlined />}
                  style={{ height: 18, width: 18, padding: 0, fontSize: 11 }}
                  onClick={e => e.stopPropagation()}
                />
              </Popconfirm>
            </Space>
          </div>
        </div>
      </Card>
    </div>
  );
}

// ─── Droppable Column ──────────────────────────────────────────
function KanbanColumn({
  column, tasks, users, labels, doneColumnKey, onEdit, onDelete, onAddClick, onToggleDone,
}: {
  column: any; tasks: any[]; users: any[]; labels: any[]; doneColumnKey: string | null;
  onEdit: (task: any) => void; onDelete: (id: string) => void;
  onAddClick: (status: string) => void; onToggleDone: (task: any) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: column.key });

  return (
    <div style={{ minWidth: 280, width: 280, flexShrink: 0 }}>
      <div
        ref={setNodeRef}
        style={{
          background: isOver ? "rgba(22, 119, 255, 0.06)" : (column.color || "#f5f5f5"),
          borderRadius: 12,
          padding: 12,
          minHeight: 400,
          border: isOver ? "2px dashed #1677ff" : "1px solid #e8e8e8",
          transition: "all 0.15s ease",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <Text strong style={{ fontSize: 13 }}>{column.label}</Text>
          <Badge count={tasks.length} color="#1677ff" />
        </div>

        <SortableContext items={tasks.map(t => t.id)} strategy={verticalListSortingStrategy}>
          {tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              users={users}
              labels={labels}
              doneColumnKey={doneColumnKey}
              onEdit={onEdit}
              onDelete={onDelete}
              onToggleDone={onToggleDone}
            />
          ))}
        </SortableContext>

        <Button
          type="dashed" block size="small" icon={<PlusOutlined />}
          onClick={() => onAddClick(column.key)}
          style={{ marginTop: 8 }}
        >
          Добавить
        </Button>
      </div>
    </div>
  );
}

// ─── Task Form Fields ─────────────────────────────────────────
function TaskFormFields({ userOptions, labelOptions, statusOptions }: {
  userOptions: any[]; labelOptions: any[]; statusOptions: any[];
}) {
  return (
    <>
      <Form.Item name="title" label="Название" rules={[{ required: true, message: "Введите название" }]}>
        <Input placeholder="Что нужно сделать?" />
      </Form.Item>
      <Form.Item name="description" label="Описание">
        <TextArea rows={2} />
      </Form.Item>
      <Form.Item name="assignee_id" label="Ответственный">
        <Select
          placeholder="Выбрать ответственного"
          options={userOptions}
          allowClear showSearch
          filterOption={(input, option) => String(option?.label).toLowerCase().includes(input.toLowerCase())}
        />
      </Form.Item>
      <Form.Item name="label_color" label="Метка">
        <Select placeholder="Выбрать метку" allowClear options={labelOptions} />
      </Form.Item>
      <div style={{ display: "flex", gap: 12 }}>
        <Form.Item name="priority" label="Приоритет" initialValue="medium" style={{ flex: 1 }}>
          <Select options={PRIORITY_OPTIONS} />
        </Form.Item>
        <Form.Item name="status" label="Колонка" style={{ flex: 1 }}>
          <Select options={statusOptions} />
        </Form.Item>
      </div>
      <Form.Item name="due_date" label="Дедлайн">
        <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
      </Form.Item>
    </>
  );
}

// ─── Activity Timeline ─────────────────────────────────────────
const ACTION_ICONS: Record<string, string> = {
  created: "✨", status_changed: "🔄", completed: "✅",
  assignee_changed: "👤", priority_changed: "🚦",
  due_date_changed: "📅", title_changed: "✏️", description_changed: "📝",
};

const ACTION_LABELS: Record<string, string> = {
  created: "Создал задачу", status_changed: "Изменил статус",
  completed: "Завершил задачу", assignee_changed: "Изменил ответственного",
  priority_changed: "Изменил приоритет", due_date_changed: "Изменил дедлайн",
  title_changed: "Переименовал задачу", description_changed: "Обновил описание",
};

const ACTIVITY_STATUS_LABELS: Record<string, string> = {
  todo: "📋 Надо сделать", in_progress: "⚡ В работе",
  review: "👀 На проверке", done: "✅ Готово",
};

const ACTIVITY_PRIORITY_LABELS: Record<string, string> = {
  low: "↓ Низкий", medium: "→ Средний", high: "↑ Высокий", urgent: "🔥 Срочно",
};

function TaskActivityTimeline({ taskId }: { taskId: string }) {
  const { data: activities = [], isLoading } = useQuery({
    queryKey: ["task-activity", taskId],
    queryFn: () => activityApi.getTaskActivity(taskId),
    enabled: !!taskId,
  });

  if (isLoading) return <div style={{ padding: 24, textAlign: "center" }}><Spin /></div>;

  if (!activities.length) {
    return (
      <div style={{ padding: 24, textAlign: "center" }}>
        <Text type="secondary">История изменений пуста</Text>
      </div>
    );
  }

  return (
    <div style={{ marginTop: 16, maxHeight: 400, overflowY: "auto", paddingRight: 8 }}>
      <Timeline
        items={(activities as any[]).map((act: any) => {
          let description = "";
          if (act.old_value && act.new_value && act.action !== "description_changed") {
            const oldLabel = ACTIVITY_STATUS_LABELS[act.old_value] || ACTIVITY_PRIORITY_LABELS[act.old_value] || act.old_value;
            const newLabel = ACTIVITY_STATUS_LABELS[act.new_value] || ACTIVITY_PRIORITY_LABELS[act.new_value] || act.new_value;
            description = `${oldLabel} → ${newLabel}`;
          }
          return {
            dot: <span style={{ fontSize: 14 }}>{ACTION_ICONS[act.action] || "📝"}</span>,
            children: (
              <div style={{ marginBottom: 4 }}>
                <Text strong style={{ fontSize: 13 }}>{act.actor_name}</Text>
                <Text type="secondary" style={{ fontSize: 12, marginLeft: 8 }}>
                  {ACTION_LABELS[act.action] || act.action}
                </Text>
                {description && <div><Text type="secondary" style={{ fontSize: 11 }}>{description}</Text></div>}
                <div>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {new Date(act.created_at).toLocaleString("ru-RU")}
                  </Text>
                </div>
              </div>
            ),
          };
        })}
      />
    </div>
  );
}

// ─── Edit Task Modal (full Trello-like) ───────────────────────
function EditTaskModal({
  task, users, labels, columns, onClose, onSave,
}: {
  task: any; users: any[]; labels: any[]; columns: any[];
  onClose: () => void; onSave: (id: string, data: any) => void;
}) {
  const [editForm] = Form.useForm();
  const [checklist, setChecklist] = useState<Array<{ text: string; done: boolean }>>(
    Array.isArray(task.checklist) ? task.checklist : []
  );
  const [coverColor, setCoverColor] = useState<string | null>(task.cover_color || null);
  const [saving, setSaving] = useState(false);

  const userOptions = users.map((u: any) => ({ value: u.id, label: `${u.last_name} ${u.first_name}` }));
  const labelOptions = labels.map((l: any) => ({
    value: l.color,
    label: (
      <Space size={6}>
        <div style={{ width: 12, height: 12, borderRadius: "50%", background: l.color, display: "inline-block" }} />
        {l.name}
      </Space>
    ),
  }));
  const statusOptions = columns.map((c: any) => ({ value: c.key, label: c.label }));

  const handleSave = async () => {
    try {
      const values = await editForm.validateFields();
      setSaving(true);
      onSave(task.id, {
        ...values,
        due_date: values.due_date?.toISOString() ?? null,
        checklist,
        cover_color: coverColor,
      });
    } catch { /* form validation error */ }
  };

  return (
    <Modal
      title={null}
      open
      onCancel={onClose}
      footer={null}
      width={680}
      destroyOnClose
    >
      {coverColor && (
        <div style={{ height: 80, background: coverColor, borderRadius: "8px 8px 0 0", margin: "-24px -24px 16px -24px" }} />
      )}
      <Tabs
        defaultActiveKey="edit"
        items={[
          {
            key: "edit",
            label: "Задача",
            children: (
              <Form
                form={editForm}
                layout="vertical"
                initialValues={{
                  ...task,
                  due_date: task.due_date ? dayjs(task.due_date) : null,
                }}
                style={{ marginTop: 8 }}
              >
                <Form.Item name="title" label="Название" rules={[{ required: true }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="description" label="Описание">
                  <TextArea rows={3} />
                </Form.Item>
                <div style={{ display: "flex", gap: 12 }}>
                  <Form.Item name="assignee_id" label="Ответственный" style={{ flex: 1 }}>
                    <Select options={userOptions} allowClear showSearch
                      filterOption={(input, option) => String(option?.label).toLowerCase().includes(input.toLowerCase())} />
                  </Form.Item>
                  <Form.Item name="label_color" label="Метка" style={{ flex: 1 }}>
                    <Select options={labelOptions} allowClear />
                  </Form.Item>
                </div>
                <div style={{ display: "flex", gap: 12 }}>
                  <Form.Item name="priority" label="Приоритет" style={{ flex: 1 }}>
                    <Select options={PRIORITY_OPTIONS} />
                  </Form.Item>
                  <Form.Item name="status" label="Колонка" style={{ flex: 1 }}>
                    <Select options={statusOptions} />
                  </Form.Item>
                  <Form.Item name="due_date" label="Дедлайн" style={{ flex: 1 }}>
                    <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
                  </Form.Item>
                </div>

                <Divider orientation="left" style={{ fontSize: 13 }}>
                  <CheckSquareOutlined /> Чеклист ({checklist.filter(c => c.done).length}/{checklist.length})
                </Divider>
                <ChecklistEditor items={checklist} onChange={setChecklist} />

                <Divider orientation="left" style={{ fontSize: 13, marginTop: 16 }}>Обложка</Divider>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
                  {COVER_COLORS.map((c) => (
                    <div
                      key={c}
                      onClick={() => setCoverColor(coverColor === c ? null : c)}
                      style={{
                        width: 32, height: 20, borderRadius: 4, background: c, cursor: "pointer",
                        border: coverColor === c ? "3px solid #000" : "2px solid transparent",
                      }}
                    />
                  ))}
                  {coverColor && (
                    <Button size="small" onClick={() => setCoverColor(null)}>Убрать</Button>
                  )}
                </div>

                <Button type="primary" block loading={saving} onClick={handleSave} style={{ marginTop: 8 }}>
                  Сохранить
                </Button>
              </Form>
            ),
          },
          {
            key: "activity",
            label: "История",
            children: <TaskActivityTimeline taskId={task.id} />,
          },
        ]}
      />
    </Modal>
  );
}

// ─── Main Page ────────────────────────────────────────────────
export const TaskBoardPage = () => {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const isAdmin = user?.role === "org_admin" || user?.role === "super_admin";

  const [selectedBoardId, setSelectedBoardId] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editTask, setEditTask] = useState<any>(null);
  const [activeTask, setActiveTask] = useState<any>(null);
  const [defaultStatus, setDefaultStatus] = useState("todo");
  const [boardSettingsOpen, setBoardSettingsOpen] = useState(false);
  const [boardsManageOpen, setBoardsManageOpen] = useState(false);
  const [createForm] = Form.useForm();

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } })
  );

  const { data: boards = [] } = useQuery({
    queryKey: ["boards"],
    queryFn: boardsApi.list,
    select: (data) => {
      if (data.length > 0 && !selectedBoardId) {
        // auto-select first board after load (via effect-free pattern)
      }
      return data;
    },
  });

  const activeBoardId = selectedBoardId || (boards.length > 0 ? (boards as any[])[0]?.id : null);

  const { data: tasks = [] } = useQuery({
    queryKey: ["tasks", activeBoardId],
    queryFn: () => tasksApi.list(undefined, activeBoardId || undefined),
    enabled: !!activeBoardId,
  });

  const { data: users = [] } = useQuery({ queryKey: ["users"], queryFn: () => usersApi.list() });
  const { data: columns = [] } = useQuery({ queryKey: ["board-columns"], queryFn: boardApi.getColumns });
  const { data: labels = [] } = useQuery({ queryKey: ["board-labels"], queryFn: boardApi.getLabels });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => tasksApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
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

  const deleteMutation = useMutation({
    mutationFn: tasksApi.delete,
    onSuccess: () => { message.success("Задача удалена"); queryClient.invalidateQueries({ queryKey: ["tasks"] }); },
  });

  const handleDragStart = (event: DragStartEvent) => {
    const task = (tasks as any[]).find((t: any) => t.id === event.active.id);
    setActiveTask(task || null);
  };

  const doneColumnKey: string | null = (columns as any[]).find((c: any) => c.is_done_column)?.key ?? null;

  const handleToggleDone = (task: any) => {
    const isDone = doneColumnKey ? task.status === doneColumnKey : task.status === "done";
    const targetStatus = isDone
      ? (columns as any[]).find((c: any) => !c.is_done_column)?.key ?? "todo"
      : doneColumnKey ?? "done";
    updateMutation.mutate({ id: task.id, data: { status: targetStatus } });
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveTask(null);
    const { active, over } = event;
    if (!over || !active) return;

    const dragged = (tasks as any[]).find((t: any) => t.id === active.id);
    if (!dragged) return;

    const overColumn = (columns as any[]).find((c: any) => c.key === over.id);
    let newStatus: string;

    if (overColumn) {
      newStatus = overColumn.key;
    } else {
      const overTask = (tasks as any[]).find((t: any) => t.id === over.id);
      newStatus = overTask?.status ?? dragged.status;
    }

    if (newStatus !== dragged.status) {
      updateMutation.mutate({ id: dragged.id, data: { status: newStatus } });
    }
  };

  const userOptions = (users as any[]).map((u: any) => ({
    value: u.id,
    label: `${u.last_name} ${u.first_name}`,
  }));

  const labelOptions = (labels as any[]).map((l: any) => ({
    value: l.color,
    label: (
      <Space size={6}>
        <div style={{ width: 12, height: 12, borderRadius: "50%", background: l.color, display: "inline-block" }} />
        {l.name}
      </Space>
    ),
  }));

  const statusOptions = (columns as any[]).map((c: any) => ({ value: c.key, label: c.label }));

  const openCreate = (status: string) => {
    setDefaultStatus(status);
    createForm.resetFields();
    createForm.setFieldsValue({ status, priority: "medium" });
    setCreateOpen(true);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Таскборд</Title>
          <div style={{ marginTop: 8 }}>
            <BoardSelector
              boards={boards as any[]}
              selectedId={activeBoardId}
              onSelect={setSelectedBoardId}
              onManage={() => setBoardsManageOpen(true)}
            />
          </div>
        </div>
        <Space>
          {isAdmin && (
            <Button icon={<SettingOutlined />} onClick={() => setBoardSettingsOpen(true)}>
              Настроить колонки
            </Button>
          )}
          <Button
            type="primary" icon={<PlusOutlined />}
            onClick={() => openCreate((columns as any[])[0]?.key || "todo")}
            disabled={!activeBoardId}
          >
            Новая задача
          </Button>
        </Space>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div style={{ display: "flex", gap: 16, overflowX: "auto", paddingBottom: 16 }}>
          {(columns as any[]).map((col: any) => (
            <KanbanColumn
              key={col.key}
              column={col}
              tasks={(tasks as any[]).filter((t: any) => t.status === col.key)}
              users={users as any[]}
              labels={labels as any[]}
              doneColumnKey={doneColumnKey}
              onEdit={setEditTask}
              onDelete={(id) => deleteMutation.mutate(id)}
              onAddClick={openCreate}
              onToggleDone={handleToggleDone}
            />
          ))}
        </div>

        <DragOverlay>
          {activeTask && (
            <div style={{ transform: "rotate(2deg)", opacity: 0.9 }}>
              <TaskCard
                task={activeTask}
                users={users as any[]}
                labels={labels as any[]}
                doneColumnKey={doneColumnKey}
                onEdit={() => {}}
                onDelete={() => {}}
                onToggleDone={() => {}}
                isDragging
              />
            </div>
          )}
        </DragOverlay>
      </DndContext>

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
        <Form
          form={createForm}
          layout="vertical"
          onFinish={(v) => createMutation.mutate({
            ...v,
            due_date: v.due_date?.toISOString() ?? null,
            board_id: activeBoardId,
          })}
          style={{ marginTop: 16 }}
        >
          <TaskFormFields userOptions={userOptions} labelOptions={labelOptions} statusOptions={statusOptions} />
        </Form>
      </Modal>

      {/* Edit Modal */}
      {editTask && (
        <EditTaskModal
          task={editTask}
          users={users as any[]}
          labels={labels as any[]}
          columns={columns as any[]}
          onClose={() => setEditTask(null)}
          onSave={(id, data) => {
            updateMutation.mutate({ id, data }, {
              onSuccess: () => { message.success("Сохранено"); setEditTask(null); },
            });
          }}
        />
      )}

      {/* Board Settings Modal */}
      <Modal
        title="Настройки колонок"
        open={boardSettingsOpen}
        onCancel={() => setBoardSettingsOpen(false)}
        footer={null}
        width={600}
      >
        <Tabs
          items={[
            {
              key: "columns",
              label: "Колонки",
              children: (
                <BoardColumnsSettings
                  columns={columns as any[]}
                  onRefresh={() => queryClient.invalidateQueries({ queryKey: ["board-columns"] })}
                />
              ),
            },
            {
              key: "labels",
              label: "Цветовые метки",
              children: (
                <BoardLabelsSettings
                  labels={labels as any[]}
                  onRefresh={() => queryClient.invalidateQueries({ queryKey: ["board-labels"] })}
                />
              ),
            },
          ]}
        />
      </Modal>

      <BoardsManageModal open={boardsManageOpen} onClose={() => setBoardsManageOpen(false)} />
    </div>
  );
};

export default TaskBoardPage;
