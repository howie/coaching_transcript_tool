import React, { useState } from 'react';
import { useI18n } from '@/contexts/i18n-context';

interface BarChartDataPoint {
  name: string;
  [key: string]: string | number;
}

interface BarChartConfig {
  [key: string]: {
    color: string;
    label: string;
    unit?: string;
  };
}

interface BarChartProps {
  data: BarChartDataPoint[];
  config: BarChartConfig;
  title?: string;
  width?: number;
  height?: number;
  showGrid?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
  orientation?: 'vertical' | 'horizontal';
  stacked?: boolean;
  yAxisLabel?: string;
  xAxisLabel?: string;
}

const BarChart: React.FC<BarChartProps> = ({
  data,
  config,
  title,
  width = 600,
  height = 300,
  showGrid = true,
  showTooltip = true,
  showLegend = true,
  orientation = 'vertical',
  stacked = false,
  yAxisLabel,
  xAxisLabel
}) => {
  const { t } = useI18n();
  const [hoveredBar, setHoveredBar] = useState<{
    x: number;
    y: number;
    data: BarChartDataPoint;
    dataKey: string;
    value: number;
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

  const padding = { top: 20, right: 30, bottom: 80, left: 60 };
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

  // Calculate scales and dimensions
  const barWidth = chartWidth / data.length * 0.8;
  const barGroupWidth = barWidth / (stacked ? 1 : dataKeys.length);
  const barSpacing = chartWidth / data.length * 0.2;

  // Calculate value ranges
  let maxValue: number;
  if (stacked) {
    maxValue = Math.max(...data.map(point => 
      dataKeys.reduce((sum, key) => sum + (Number(point[key]) || 0), 0)
    ));
  } else {
    const allValues = data.flatMap(point => 
      dataKeys.map(key => Number(point[key]) || 0)
    );
    maxValue = Math.max(...allValues);
  }
  
  const minValue = 0;
  const valueRange = maxValue - minValue || 1;

  // Scales
  const xScale = (index: number) => (index * (barWidth + barSpacing)) + barSpacing / 2;
  const yScale = (value: number) => chartHeight - ((value - minValue) / valueRange) * chartHeight;

  // Generate bars
  const bars: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
    color: string;
    dataKey: string;
    data: BarChartDataPoint;
    value: number;
    index: number;
  }> = [];

  data.forEach((point, dataIndex) => {
    if (stacked) {
      // Stacked bars
      let stackedY = 0;
      dataKeys.forEach((dataKey, keyIndex) => {
        const value = Number(point[dataKey]) || 0;
        const barHeight = (value / valueRange) * chartHeight;
        
        bars.push({
          x: xScale(dataIndex),
          y: yScale(stackedY + value),
          width: barWidth,
          height: barHeight,
          color: config[dataKey].color,
          dataKey,
          data: point,
          value,
          index: dataIndex
        });
        
        stackedY += value;
      });
    } else {
      // Grouped bars
      dataKeys.forEach((dataKey, keyIndex) => {
        const value = Number(point[dataKey]) || 0;
        const barHeight = (value / valueRange) * chartHeight;
        
        bars.push({
          x: xScale(dataIndex) + (keyIndex * barGroupWidth),
          y: yScale(value),
          width: barGroupWidth * 0.9,
          height: barHeight,
          color: config[dataKey].color,
          dataKey,
          data: point,
          value,
          index: dataIndex
        });
      });
    }
  });

  // Generate grid lines
  const gridLines = [];
  if (showGrid) {
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
  }

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
          onMouseLeave={() => setHoveredBar(null)}
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
          
          {/* Bars */}
          {bars.map((bar, index) => (
            <rect
              key={`${bar.dataKey}-${bar.index}-${index}`}
              x={bar.x + padding.left}
              y={bar.y + padding.top}
              width={bar.width}
              height={bar.height}
              fill={bar.color}
              className="cursor-pointer hover:opacity-80 transition-opacity duration-200"
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setHoveredBar({
                  x: rect.left + rect.width / 2,
                  y: rect.top,
                  data: bar.data,
                  dataKey: bar.dataKey,
                  value: bar.value
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
            const x = xScale(index) + barWidth / 2 + padding.left;
            return (
              <text
                key={`x-label-${index}`}
                x={x}
                y={padding.top + chartHeight + 20}
                textAnchor="middle"
                className="text-xs fill-content-secondary"
                transform={point.name.length > 8 ? `rotate(-45 ${x} ${padding.top + chartHeight + 20})` : undefined}
              >
                {point.name.length > 12 ? `${point.name.substring(0, 12)}...` : point.name}
              </text>
            );
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
        {showTooltip && hoveredBar && (
          <div
            className="absolute z-10 bg-surface border border-border rounded-lg shadow-lg p-3 pointer-events-none"
            style={{
              left: `${hoveredBar.x}px`,
              top: `${hoveredBar.y - 10}px`,
              transform: 'translate(-50%, -100%)'
            }}
          >
            <div className="text-sm">
              <div className="font-medium text-content-primary mb-1">
                {hoveredBar.data.name}
              </div>
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: config[hoveredBar.dataKey].color }}
                />
                <span className="text-content-secondary">
                  {config[hoveredBar.dataKey].label}:
                </span>
                <span className="font-medium text-content-primary">
                  {formatValue(hoveredBar.value, hoveredBar.dataKey)}
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

export default BarChart;