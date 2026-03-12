import { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Bar,
  ReferenceLine,
} from 'recharts';
import type { OHLCVPoint, TechnicalAnalysis } from '../types/portfolio';

interface PriceChartProps {
  data: OHLCVPoint[];
  technical?: TechnicalAnalysis;
  showVolume?: boolean;
  showSMA?: boolean;
  height?: number;
}

export const PriceChart = ({
  data,
  technical,
  showVolume = true,
  showSMA = true,
  height = 400,
}: PriceChartProps) => {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      date: new Date(d.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      fullDate: new Date(d.timestamp).toLocaleDateString(),
      price: d.close,
      volume: d.volume,
      high: d.high,
      low: d.low,
      open: d.open,
    }));
  }, [data]);

  const smaData = useMemo(() => {
    if (!showSMA || data.length < 50) return chartData;
    
    const prices = data.map((d) => d.close);
    const sma20: (number | null)[] = [];
    const sma50: (number | null)[] = [];
    
    for (let i = 0; i < prices.length; i++) {
      if (i >= 19) {
        const sum20 = prices.slice(i - 19, i + 1).reduce((a, b) => a + b, 0);
        sma20.push(sum20 / 20);
      } else {
        sma20.push(null);
      }
      
      if (i >= 49) {
        const sum50 = prices.slice(i - 49, i + 1).reduce((a, b) => a + b, 0);
        sma50.push(sum50 / 50);
      } else {
        sma50.push(null);
      }
    }
    
    return chartData.map((d, i) => ({
      ...d,
      sma20: sma20[i],
      sma50: sma50[i],
    }));
  }, [data, chartData, showSMA]);

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{value: number; name: string; color: string; payload: {fullDate: string}}> }) => {
    if (active && payload && payload.length) {
      const data = payload[0]?.payload;
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
          <p className="text-slate-300 text-sm mb-2">{data?.fullDate}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value?.toFixed(2)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const priceColor = '#10b981';
  const sma20Color = '#f59e0b';
  const sma50Color = '#8b5cf6';

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={showVolume ? height - 100 : height}>
        <ComposedChart data={smaData}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={priceColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={priceColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          
          <XAxis
            dataKey="date"
            stroke="#334155"
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={{ stroke: '#334155' }}
            axisLine={{ stroke: '#334155' }}
            minTickGap={30}
          />
          
          <YAxis
            stroke="#334155"
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={{ stroke: '#334155' }}
            axisLine={{ stroke: '#334155' }}
            domain={['auto', 'auto']}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
            width={60}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          {technical?.support_resistance && (
            <>
              <ReferenceLine
                y={technical.support_resistance.resistance_1}
                stroke="#f43f5e"
                strokeDasharray="3 3"
                strokeOpacity={0.6}
                label={{ value: 'R1', fill: '#f43f5e', fontSize: 11, position: 'right' }}
              />
              <ReferenceLine
                y={technical.support_resistance.support_1}
                stroke="#10b981"
                strokeDasharray="3 3"
                strokeOpacity={0.6}
                label={{ value: 'S1', fill: '#10b981', fontSize: 11, position: 'right' }}
              />
            </>
          )}
          
          <Area
            type="monotone"
            dataKey="price"
            stroke={priceColor}
            strokeWidth={2}
            fill="url(#priceGradient)"
            name="Price"
          />
          
          {showSMA && (
            <>
              <Line
                type="monotone"
                dataKey="sma20"
                stroke={sma20Color}
                strokeWidth={1.5}
                dot={false}
                name="SMA 20"
                connectNulls
              />
              <Line
                type="monotone"
                dataKey="sma50"
                stroke={sma50Color}
                strokeWidth={1.5}
                dot={false}
                name="SMA 50"
                connectNulls
              />
            </>
          )}
        </ComposedChart>
      </ResponsiveContainer>
      
      {showVolume && (
        <ResponsiveContainer width="100%" height={80}>
          <ComposedChart data={chartData}>
            <XAxis dataKey="date" hide />
            <YAxis hide />
            <Bar
              dataKey="volume"
              fill="#334155"
              opacity={0.5}
              name="Volume"
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
