import React, { useState } from 'react';
import { useI18n } from '@/contexts/i18n-context';

interface LineChartDataPoint {
  date: string;
  [key: string]: string | number;
}

interface LineChartConfig {
  [key: string]: {
    color: string;
    label: string;
    unit?: string;
  };
}

interface LineChartProps {
  data: LineChartDataPoint[];
  config: LineChartConfig;
  title?: string;
  width?: number;
  height?: number;
  showGrid?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
  yAxisLabel?: string;
  xAxisLabel?: string;
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  config,
  title,
  width = 600,
  height = 300,
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  yAxisLabel,
  xAxisLabel
}) => {
  const { t } = useI18n();
  const [hoveredPoint, setHoveredPoint] = useState<{
    x: number;
    y: number;
    data: LineChartDataPoint;
    dataKey: string;
  } | null>(null);

  if (!data || data.length === 0) {
    return (
      <div className="bg-dashboard-card border border-border rounded-lg p-6">
        {title && (
          <h3 className="text-lg font-semibold text-content-primary mb-4">{title}</h3>
        )}
        <div className="flex items-center justify-center h-48 text-content-secondary">
          {t('common.noData')}
        </div>
      </div>
    );
  }

  const padding = { top: 20, right: 30, bottom: 60, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Get all numeric data keys from config
  const dataKeys = Object.keys(config).filter(key => 
    data.some(point => typeof point[key] === 'number')
  );

  if (dataKeys.length === 0) {
    return (
      <div className="bg-dashboard-card border border-border rounded-lg p-6">
        {title && (
          <h3 className="text-lg font-semibold text-content-primary mb-4">{title}</h3>
        )}
        <div className="flex items-center justify-center h-48 text-content-secondary">
          {t('common.noValidData')}
        </div>
      </div>
    );
  }

  // Calculate scales
  const xScale = (index: number) => (index / (data.length - 1)) * chartWidth;
  
  // Get min/max values for all data keys
  const allValues = data.flatMap(point => 
    dataKeys.map(key => Number(point[key]) || 0)
  );
  const minValue = Math.min(0, ...allValues);
  const maxValue = Math.max(...allValues);
  const valueRange = maxValue - minValue || 1;
  
  const yScale = (value: number) => 
    chartHeight - ((value - minValue) / valueRange) * chartHeight;

  // Generate lines for each data key
  const lines = dataKeys.map(dataKey => {
    const pathData = data
      .map((point, index) => {
        const x = xScale(index);
        const y = yScale(Number(point[dataKey]) || 0);
        return `${index === 0 ? 'M' : 'L'} ${x + padding.left} ${y + padding.top}`;
      })
      .join(' ');

    return {
      dataKey,
      path: pathData,
      color: config[dataKey].color,
      label: config[dataKey].label
    };
  });

  // Generate grid lines
  const gridLines = [];
  if (showGrid) {
    // Horizontal grid lines
    const yTicks = 5;
    for (let i = 0; i <= yTicks; i++) {
      const y = (i / yTicks) * chartHeight + padding.top;
      gridLines.push(
        <line
          key={`h-${i}`}
          x1={padding.left}
          y1={y}
          x2={padding.left + chartWidth}
          y2={y}
          stroke="currentColor"
          strokeWidth="1"
          className="stroke-border opacity-30"
        />
      );
    }

    // Vertical grid lines
    const xTicks = Math.min(data.length - 1, 6);
    for (let i = 0; i <= xTicks; i++) {
      const x = (i / xTicks) * chartWidth + padding.left;
      gridLines.push(
        <line
          key={`v-${i}`}
          x1={x}
          y1={padding.top}
          x2={x}
          y2={padding.top + chartHeight}
          stroke="currentColor"
          strokeWidth="1"
          className="stroke-border opacity-30"
        />
      );
    }
  }

  // Generate data points for hover interaction
  const dataPoints = data.flatMap((point, index) =>
    dataKeys.map(dataKey => ({
      x: xScale(index) + padding.left,
      y: yScale(Number(point[dataKey]) || 0) + padding.top,
      data: point,
      dataKey,
      index
    }))
  );

  // Format date for display
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  // Format value for display
  const formatValue = (value: number, dataKey: string) => {
    const unit = config[dataKey]?.unit || '';
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}k${unit}`;
    }
    return `${value.toFixed(1)}${unit}`;
  };

  return (
    <div className="bg-dashboard-card border border-border rounded-lg p-6">
      {title && (
        <h3 className="text-lg font-semibold text-content-primary mb-6">{title}</h3>
      )}
      
      <div className="relative">
        <svg 
          width={width} 
          height={height}
          className="overflow-visible"
          onMouseLeave={() => setHoveredPoint(null)}
        >
          {/* Grid lines */}
          {gridLines}
          
          {/* Y-axis */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={padding.top + chartHeight}
            stroke="currentColor"
            strokeWidth="2"
            className="stroke-content-secondary"
          />
          
          {/* X-axis */}
          <line
            x1={padding.left}
            y1={padding.top + chartHeight}
            x2={padding.left + chartWidth}
            y2={padding.top + chartHeight}
            stroke="currentColor"
            strokeWidth="2"
            className="stroke-content-secondary"
          />
          
          {/* Data lines */}
          {lines.map(line => (
            <path
              key={line.dataKey}
              d={line.path}
              fill="none"
              stroke={line.color}
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="drop-shadow-sm"
            />
          ))}
          
          {/* Data points */}
          {dataPoints.map((point, index) => (
            <circle
              key={`${point.dataKey}-${point.index}`}
              cx={point.x}
              cy={point.y}
              r="4"
              fill={config[point.dataKey].color}
              stroke="white"
              strokeWidth="2"
              className="cursor-pointer hover:r-6 transition-all duration-200"
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setHoveredPoint({
                  x: rect.left + rect.width / 2,
                  y: rect.top,
                  data: point.data,
                  dataKey: point.dataKey
                });
              }}
            />
          ))}
          
          {/* Y-axis labels */}
          {Array.from({ length: 6 }, (_, i) => {
            const value = minValue + (valueRange * i / 5);
            const y = yScale(value) + padding.top;
            return (
              <text
                key={`y-label-${i}`}
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                className="text-xs fill-content-secondary"
              >
                {formatValue(value, dataKeys[0])}
              </text>
            );
          })}
          
          {/* X-axis labels */}
          {data.map((point, index) => {
            if (index % Math.ceil(data.length / 6) === 0 || index === data.length - 1) {
              const x = xScale(index) + padding.left;
              return (
                <text
                  key={`x-label-${index}`}
                  x={x}
                  y={padding.top + chartHeight + 20}
                  textAnchor="middle"
                  className="text-xs fill-content-secondary"
                >
                  {formatDate(point.date)}
                </text>
              );
            }
            return null;
          })}
          
          {/* Axis labels */}
          {yAxisLabel && (
            <text
              x={20}
              y={height / 2}
              textAnchor="middle"
              transform={`rotate(-90 20 ${height / 2})`}
              className="text-sm fill-content-secondary font-medium"
            >
              {yAxisLabel}
            </text>
          )}
          
          {xAxisLabel && (
            <text
              x={width / 2}
              y={height - 10}
              textAnchor="middle"
              className="text-sm fill-content-secondary font-medium"
            >
              {xAxisLabel}
            </text>
          )}
        </svg>
        
        {/* Tooltip */}
        {showTooltip && hoveredPoint && (
          <div
            className="absolute z-10 bg-surface border border-border rounded-lg shadow-lg p-3 pointer-events-none"
            style={{
              left: `${hoveredPoint.x}px`,
              top: `${hoveredPoint.y - 10}px`,
              transform: 'translate(-50%, -100%)'
            }}
          >
            <div className="text-sm">
              <div className="font-medium text-content-primary mb-1">
                {formatDate(hoveredPoint.data.date)}
              </div>
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: config[hoveredPoint.dataKey].color }}
                />
                <span className="text-content-secondary">
                  {config[hoveredPoint.dataKey].label}:
                </span>
                <span className="font-medium text-content-primary">
                  {formatValue(Number(hoveredPoint.data[hoveredPoint.dataKey]), hoveredPoint.dataKey)}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Legend */}
      {showLegend && (
        <div className="flex flex-wrap gap-4 mt-4 justify-center">
          {dataKeys.map(dataKey => (
            <div key={dataKey} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: config[dataKey].color }}
              />
              <span className="text-sm text-content-secondary">
                {config[dataKey].label}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default LineChart;