import { Card, Typography } from "antd";

const { Title, Text } = Typography;

export const ImportsPage = () => (
  <div>
    <Title level={3}>Импорт данных</Title>
    <Card bordered={false} style={{ boxShadow: "0 2px 8px rgba(0,0,0,0.06)" }}>
      <Text type="secondary">Импорт из Excel и 1С. В разработке.</Text>
    </Card>
  </div>
);
