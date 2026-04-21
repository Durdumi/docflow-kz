import { Card, Typography } from "antd";

const { Title, Text } = Typography;

export const UsersPage = () => (
  <div>
    <Title level={3}>Пользователи</Title>
    <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
      <Text type="secondary">Управление пользователями организации. В разработке.</Text>
    </Card>
  </div>
);
