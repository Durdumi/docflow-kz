import { useState } from "react";
import {
  Button, Calendar, Card, Form, Input,
  Modal, Typography, message, DatePicker,
} from "antd";
import { PlusOutlined, DeleteOutlined } from "@ant-design/icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { calendarApi } from "@/api/tasks";
import dayjs, { Dayjs } from "dayjs";
import type { CalendarMode } from "antd/es/calendar/generateCalendar";

const { Title, Text } = Typography;
const { TextArea } = Input;

const EVENT_COLORS = [
  { value: "#1677ff", label: "Синий" },
  { value: "#52c41a", label: "Зелёный" },
  { value: "#ff4d4f", label: "Красный" },
  { value: "#faad14", label: "Жёлтый" },
  { value: "#722ed1", label: "Фиолетовый" },
  { value: "#13c2c2", label: "Бирюзовый" },
];

export const CalendarPage = () => {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
  const [currentMonth, setCurrentMonth] = useState({
    year: dayjs().year(),
    month: dayjs().month() + 1,
  });
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedEvents, setSelectedEvents] = useState<any[]>([]);
  const [eventsModalOpen, setEventsModalOpen] = useState(false);
  const [selectedColor, setSelectedColor] = useState("#1677ff");
  const [form] = Form.useForm();

  const { data: events = [] } = useQuery({
    queryKey: ["calendar", currentMonth.year, currentMonth.month],
    queryFn: () => calendarApi.list(currentMonth.year, currentMonth.month),
  });

  const createMutation = useMutation({
    mutationFn: calendarApi.create,
    onSuccess: () => {
      message.success("Событие добавлено");
      setCreateOpen(false);
      form.resetFields();
      setSelectedColor("#1677ff");
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
    onError: () => message.error("Ошибка при создании события"),
  });

  const deleteMutation = useMutation({
    mutationFn: calendarApi.delete,
    onSuccess: () => {
      message.success("Событие удалено");
      queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
  });

  const getEventsForDate = (date: Dayjs) =>
    events.filter((e: any) => dayjs(e.start_date).isSame(date, "day"));

  const dateCellRender = (date: Dayjs) => {
    const dayEvents = getEventsForDate(date);
    return (
      <div style={{ overflow: "hidden" }}>
        {dayEvents.slice(0, 2).map((event: any) => (
          <div
            key={event.id}
            style={{
              fontSize: 11,
              background: event.color,
              color: "white",
              borderRadius: 3,
              padding: "1px 4px",
              marginBottom: 2,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {event.title}
          </div>
        ))}
        {dayEvents.length > 2 && (
          <Text style={{ fontSize: 10, color: "#1677ff" }}>
            +{dayEvents.length - 2} ещё
          </Text>
        )}
      </div>
    );
  };

  const onSelect = (date: Dayjs) => {
    setSelectedDate(date);
    const dayEvents = getEventsForDate(date);
    if (dayEvents.length > 0) {
      setSelectedEvents(dayEvents);
      setEventsModalOpen(true);
    } else {
      form.setFieldsValue({ start_date: date });
      setCreateOpen(true);
    }
  };

  const onPanelChange = (date: Dayjs, _mode: CalendarMode) => {
    setCurrentMonth({ year: date.year(), month: date.month() + 1 });
  };

  const onCreateFinish = (values: any) => {
    createMutation.mutate({
      ...values,
      color: selectedColor,
      start_date: (values.start_date || selectedDate).toISOString(),
      all_day: true,
    });
  };

  const handleDelete = (eventId: string) => {
    deleteMutation.mutate(eventId);
    setSelectedEvents(prev => prev.filter(e => e.id !== eventId));
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Календарь</Title>
          <Text type="secondary">События и дедлайны организации</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => { form.resetFields(); setSelectedColor("#1677ff"); setCreateOpen(true); }}
        >
          Добавить событие
        </Button>
      </div>

      <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
        <Calendar
          cellRender={(date, info) => {
            if (info.type === "date") return dateCellRender(date);
            return null;
          }}
          onSelect={onSelect}
          onPanelChange={onPanelChange}
        />
      </Card>

      {/* Create Event Modal */}
      <Modal
        title="Новое событие"
        open={createOpen}
        onCancel={() => { setCreateOpen(false); form.resetFields(); setSelectedColor("#1677ff"); }}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" onFinish={onCreateFinish} style={{ marginTop: 16 }}>
          <Form.Item name="title" label="Название" rules={[{ required: true, message: "Введите название" }]}>
            <Input placeholder="Название события" />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <TextArea rows={2} />
          </Form.Item>
          <Form.Item name="start_date" label="Дата">
            <DatePicker style={{ width: "100%" }} format="DD.MM.YYYY" />
          </Form.Item>
          <Form.Item label="Цвет">
            <div style={{ display: "flex", gap: 8 }}>
              {EVENT_COLORS.map(c => (
                <div
                  key={c.value}
                  onClick={() => setSelectedColor(c.value)}
                  title={c.label}
                  style={{
                    width: 24,
                    height: 24,
                    borderRadius: "50%",
                    background: c.value,
                    cursor: "pointer",
                    border: selectedColor === c.value ? "3px solid #000" : "2px solid transparent",
                    flexShrink: 0,
                  }}
                />
              ))}
            </div>
          </Form.Item>
        </Form>
      </Modal>

      {/* Events for selected date */}
      <Modal
        title={`События: ${selectedDate.format("DD MMMM YYYY")}`}
        open={eventsModalOpen}
        onCancel={() => setEventsModalOpen(false)}
        footer={[
          <Button
            key="add"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEventsModalOpen(false);
              form.setFieldsValue({ start_date: selectedDate });
              setCreateOpen(true);
            }}
          >
            Добавить
          </Button>,
          <Button key="close" onClick={() => setEventsModalOpen(false)}>
            Закрыть
          </Button>,
        ]}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
          {selectedEvents.map((event: any) => (
            <Card key={event.id} size="small" style={{ borderLeft: `4px solid ${event.color}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div>
                  <Text strong>{event.title}</Text>
                  {event.description && (
                    <Text type="secondary" style={{ display: "block", fontSize: 12 }}>
                      {event.description}
                    </Text>
                  )}
                </div>
                <Button
                  size="small"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDelete(event.id)}
                />
              </div>
            </Card>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default CalendarPage;
