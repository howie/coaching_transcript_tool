import React from 'react';

interface PieChartData {
  name: string;
  value: number;
}

interface PieChartProps {
  data: PieChartData[];
  title: string;
  width?: number;
  height?: number;
}

const PieChart: React.FC<PieChartProps> = ({ 
  data, 
  title, 
  width = 200, 
  height = 200 
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-4">
        <h3 className="text-lg font-medium text-content-primary mb-4">{title}</h3>
        <div className="flex items-center justify-center h-32 text-content-secondary">
          無數據
        </div>
      </div>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  if (total === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-4">
        <h3 className="text-lg font-medium text-content-primary mb-4">{title}</h3>
        <div className="flex items-center justify-center h-32 text-content-secondary">
          無數據
        </div>
      </div>
    );
  }

  const colors = [
    '#3B82F6', // blue
    '#10B981', // emerald
    '#F59E0B', // amber
    '#EF4444', // red
    '#8B5CF6', // violet
    '#F97316', // orange
    '#06B6D4', // cyan
    '#84CC16'  // lime
  ];

  let currentAngle = 0;
  const radius = Math.min(width, height) / 2 - 20;
  const centerX = width / 2;
  const centerY = height / 2;

  const pieSlices = data.map((item, index) => {
    const percentage = (item.value / total) * 100;
    const angle = (item.value / total) * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + angle;
    
    // Special case for 100% (full circle)
    if (percentage === 100 && data.length === 1) {
      // Draw a full circle using two arcs
      const pathData = [
        `M ${centerX} ${centerY - radius}`,
        `A ${radius} ${radius} 0 0 1 ${centerX} ${centerY + radius}`,
        `A ${radius} ${radius} 0 0 1 ${centerX} ${centerY - radius}`,
        'Z'
      ].join(' ');
      
      return {
        path: pathData,
        color: colors[index % colors.length],
        name: item.name,
        value: item.value,
        percentage: percentage.toFixed(1)
      };
    }
    
    const startAngleRad = (startAngle * Math.PI) / 180;
    const endAngleRad = (endAngle * Math.PI) / 180;
    
    const x1 = centerX + radius * Math.cos(startAngleRad);
    const y1 = centerY + radius * Math.sin(startAngleRad);
    const x2 = centerX + radius * Math.cos(endAngleRad);
    const y2 = centerY + radius * Math.sin(endAngleRad);
    
    const largeArcFlag = angle > 180 ? 1 : 0;
    
    const pathData = [
      `M ${centerX} ${centerY}`,
      `L ${x1} ${y1}`,
      `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
      'Z'
    ].join(' ');
    
    currentAngle += angle;
    
    return {
      path: pathData,
      color: colors[index % colors.length],
      name: item.name,
      value: item.value,
      percentage: percentage.toFixed(1)
    };
  });

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <h3 className="text-lg font-medium text-content-primary mb-4">{title}</h3>
      <div className="flex flex-col items-center">
        <svg width={width} height={height} className="mb-4">
          {pieSlices.map((slice, index) => (
            <path
              key={index}
              d={slice.path}
              fill={slice.color}
              stroke="currentColor"
              strokeWidth="1"
              className="transition-opacity hover:opacity-80 stroke-surface"
            />
          ))}
        </svg>
        
        {/* Legend */}
        <div className="grid grid-cols-1 gap-2 text-sm">
          {pieSlices.map((slice, index) => (
            <div key={index} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-sm"
                style={{ backgroundColor: slice.color }}
              />
              <span className="text-content-primary">
                {slice.name}: {slice.value} ({slice.percentage}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PieChart;