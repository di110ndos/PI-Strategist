/**
 * Reusable KPI Card component with colored status border, optional icon and trend.
 */

import {
  Card,
  CardBody,
  HStack,
  Text,
  Icon,
  Tooltip,
  useColorModeValue,
} from '@chakra-ui/react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface KPICardProps {
  label: string;
  value: string | number;
  helpText?: string;
  status?: 'success' | 'warning' | 'error' | 'info';
  icon?: React.ElementType;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
}

const STATUS_COLORS: Record<string, string> = {
  success: 'green.400',
  warning: 'orange.400',
  error: 'red.400',
  info: 'blue.400',
};

const TREND_ICONS = { up: TrendingUp, down: TrendingDown, stable: Minus };
const TREND_COLORS = { up: 'green.500', down: 'red.500', stable: 'gray.500' };

export default function KPICard({
  label,
  value,
  helpText,
  status = 'info',
  icon,
  trend,
  trendValue,
}: KPICardProps) {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = STATUS_COLORS[status];

  const content = (
    <Card bg={cardBg} borderLeft="4px solid" borderLeftColor={borderColor}>
      <CardBody py={4} px={4}>
        {icon && (
          <Icon as={icon} boxSize={4} color={borderColor} mb={1} />
        )}
        <Text fontSize="2xl" fontWeight="bold" lineHeight="short">
          {value}
        </Text>
        <Text fontSize="xs" color="gray.500" mt={0.5}>
          {label}
        </Text>
        {trend && (
          <HStack spacing={1} mt={1}>
            <Icon as={TREND_ICONS[trend]} boxSize={3} color={TREND_COLORS[trend]} />
            {trendValue && (
              <Text fontSize="xs" color={TREND_COLORS[trend]}>
                {trendValue}
              </Text>
            )}
          </HStack>
        )}
      </CardBody>
    </Card>
  );

  return helpText ? (
    <Tooltip label={helpText} fontSize="xs" placement="top" hasArrow>
      {content}
    </Tooltip>
  ) : (
    content
  );
}
