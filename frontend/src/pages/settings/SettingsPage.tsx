import { Card, Typography } from "antd";

const { Title, Text } = Typography;

export const SettingsPage = () => (
  <div>
    <Title level={3}>Настройки</Title>
    <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
      <Text type="secondary">Раздел в разработке. Будет доступен в следующей версии.</Text>
    </Card>
  </div>
);
