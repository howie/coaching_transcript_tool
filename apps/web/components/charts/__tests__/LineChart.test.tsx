import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LineChart from '../LineChart';

// Mock i18n context
const mockT = (key: string) => key;
jest.mock('@/contexts/i18n-context', () => ({
  useI18n: () => ({ t: mockT })
}));

describe('LineChart', () => {
  const mockData = [
    { date: '2024-01-01', sessions: 10, minutes: 120, cost: 5.50 },
    { date: '2024-01-02', sessions: 15, minutes: 180, cost: 8.25 },
    { date: '2024-01-03', sessions: 8, minutes: 90, cost: 4.10 },
    { date: '2024-01-04', sessions: 20, minutes: 240, cost: 11.00 }
  ];

  const mockConfig = {
    sessions: { color: '#FFB800', label: 'Sessions', unit: '' },
    minutes: { color: '#4ECDC4', label: 'Minutes', unit: ' min' },
    cost: { color: '#9B59B6', label: 'Cost', unit: ' USD' }
  };

  it('renders chart with data', () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        title="Usage Trends"
      />
    );

    expect(screen.getByText('Usage Trends')).toBeInTheDocument();
    
    // Check for SVG element
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
    
    // Check for data lines (paths)
    const paths = document.querySelectorAll('path');
    expect(paths.length).toBeGreaterThan(0);
  });

  it('shows no data message when data is empty', () => {
    render(
      <LineChart
        data={[]}
        config={mockConfig}
        title="Empty Chart"
      />
    );

    expect(screen.getByText('Empty Chart')).toBeInTheDocument();
    expect(screen.getByText('common.noData')).toBeInTheDocument();
  });

  it('shows no valid data message when data has no numeric values', () => {
    const invalidData = [
      { date: '2024-01-01', label: 'test' },
      { date: '2024-01-02', label: 'test2' }
    ];

    render(
      <LineChart
        data={invalidData}
        config={mockConfig}
        title="Invalid Data Chart"
      />
    );

    expect(screen.getByText('Invalid Data Chart')).toBeInTheDocument();
    expect(screen.getByText('common.noValidData')).toBeInTheDocument();
  });

  it('renders without title', () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
      />
    );

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('renders with custom dimensions', () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        width={800}
        height={400}
      />
    );

    const svg = document.querySelector('svg');
    expect(svg).toHaveAttribute('width', '800');
    expect(svg).toHaveAttribute('height', '400');
  });

  it('renders grid lines when showGrid is true', () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        showGrid={true}
      />
    );

    const lines = document.querySelectorAll('line');
    expect(lines.length).toBeGreaterThan(2); // Should have grid lines plus axes
  });

  it('renders legend when showLegend is true', () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        showLegend={true}
      />
    );

    expect(screen.getByText('Sessions')).toBeInTheDocument();
    expect(screen.getByText('Minutes')).toBeInTheDocument();
    expect(screen.getByText('Cost')).toBeInTheDocument();
  });

  it('renders axis labels when provided', () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        xAxisLabel="Date"
        yAxisLabel="Usage"
      />
    );

    const texts = document.querySelectorAll('text');
    const textContents = Array.from(texts).map(text => text.textContent);
    
    expect(textContents).toContain('Date');
    expect(textContents).toContain('Usage');
  });

  it('shows tooltip on hover', async () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        showTooltip={true}
      />
    );

    // Find data points (circles)
    const circles = document.querySelectorAll('circle');
    expect(circles.length).toBeGreaterThan(0);

    // Hover over the first data point
    fireEvent.mouseEnter(circles[0]);

    // Wait for tooltip to appear
    await waitFor(() => {
      const tooltip = document.querySelector('[class*="absolute"]');
      expect(tooltip).toBeInTheDocument();
    });
  });

  it('formats large values correctly', () => {
    const largeValueData = [
      { date: '2024-01-01', sessions: 1500, minutes: 12000 },
      { date: '2024-01-02', sessions: 2200, minutes: 15000 }
    ];

    const largeValueConfig = {
      sessions: { color: '#FFB800', label: 'Sessions', unit: '' },
      minutes: { color: '#4ECDC4', label: 'Minutes', unit: ' min' }
    };

    render(
      <LineChart
        data={largeValueData}
        config={largeValueConfig}
      />
    );

    // Check that values are formatted with 'k' suffix
    const texts = document.querySelectorAll('text');
    const textContents = Array.from(texts).map(text => text.textContent);
    
    // Should have some values with 'k' formatting
    const hasKFormatting = textContents.some(text => text && text.includes('k'));
    expect(hasKFormatting).toBe(true);
  });

  it('handles single data point correctly', () => {
    const singlePointData = [
      { date: '2024-01-01', sessions: 10, minutes: 120 }
    ];

    render(
      <LineChart
        data={singlePointData}
        config={mockConfig}
      />
    );

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
    
    // Should still render paths and circles
    const paths = document.querySelectorAll('path');
    const circles = document.querySelectorAll('circle');
    expect(paths.length).toBeGreaterThan(0);
    expect(circles.length).toBeGreaterThan(0);
  });

  it('handles zero values correctly', () => {
    const zeroValueData = [
      { date: '2024-01-01', sessions: 0, minutes: 0 },
      { date: '2024-01-02', sessions: 5, minutes: 60 }
    ];

    render(
      <LineChart
        data={zeroValueData}
        config={mockConfig}
      />
    );

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('removes tooltip on mouse leave', async () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        showTooltip={true}
      />
    );

    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();

    // Hover over chart area
    const circles = document.querySelectorAll('circle');
    if (circles.length > 0) {
      fireEvent.mouseEnter(circles[0]);
      
      // Wait for tooltip to appear
      await waitFor(() => {
        const tooltip = document.querySelector('[class*="absolute"]');
        expect(tooltip).toBeInTheDocument();
      });

      // Mouse leave from the SVG
      fireEvent.mouseLeave(svg!);

      // Tooltip should be removed
      await waitFor(() => {
        const tooltip = document.querySelector('[class*="absolute"]');
        expect(tooltip).not.toBeInTheDocument();
      });
    }
  });

  it('formats dates correctly in tooltip and axis', () => {
    render(
      <LineChart
        data={mockData}
        config={mockConfig}
        showTooltip={true}
      />
    );

    // Check for formatted dates in axis labels
    const texts = document.querySelectorAll('text');
    const textContents = Array.from(texts).map(text => text.textContent);
    
    // Should have some formatted dates (e.g., "Jan 1", "Jan 2")
    const hasDateFormatting = textContents.some(text => 
      text && /Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec/.test(text)
    );
    expect(hasDateFormatting).toBe(true);
  });

  it('respects showGrid, showTooltip, and showLegend props', () => {
    const { rerender } = render(
      <LineChart
        data={mockData}
        config={mockConfig}
        showGrid={false}
        showTooltip={false}
        showLegend={false}
      />
    );

    // Without showLegend, legend text should not be present
    expect(screen.queryByText('Sessions')).not.toBeInTheDocument();

    // Rerender with showLegend true
    rerender(
      <LineChart
        data={mockData}
        config={mockConfig}
        showGrid={true}
        showTooltip={true}
        showLegend={true}
      />
    );

    // Now legend should be present
    expect(screen.getByText('Sessions')).toBeInTheDocument();
  });
});