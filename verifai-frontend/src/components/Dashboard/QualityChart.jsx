import React, { useState } from 'react';
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
} from 'recharts';
import { Calendar, TrendingUp, BarChart3 } from 'lucide-react';

const QualityChart = ({ data, title = 'Quality Score Trend', rangeLabel = '30D' }) => {
  const [chartType, setChartType] = useState('line');

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="rounded-lg bg-white p-3 shadow-lg">
          <p className="text-sm font-medium text-gray-600">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(3)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="rounded-xl bg-white p-5 shadow-lg">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
          <p className="text-sm text-gray-500">Quality scores over time</p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex rounded-lg border border-gray-200">
            <button
              onClick={() => setChartType('line')}
              className={`rounded-l-lg px-3 py-1.5 text-sm transition-colors ${
                chartType === 'line'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <TrendingUp className="h-4 w-4" />
            </button>
            <button
              onClick={() => setChartType('area')}
              className={`rounded-r-lg px-3 py-1.5 text-sm transition-colors ${
                chartType === 'area'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <BarChart3 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        {chartType === 'line' ? (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickFormatter={(value) => value.toFixed(1)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
              activeDot={{ r: 6 }}
              name="Quality Score"
            />
            <Line
              type="monotone"
              dataKey="movingAverage"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="5 5"
              name="7-Day Average"
            />
            <Brush dataKey="date" height={30} stroke="#3b82f6" fill="#f3f4f6" />
          </LineChart>
        ) : (
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fill: '#6b7280', fontSize: 12 }}
              tickFormatter={(value) => value.toFixed(1)}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.1}
              name="Quality Score"
            />
            <Area
              type="monotone"
              dataKey="movingAverage"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.05}
              name="7-Day Average"
            />
          </AreaChart>
        )}
      </ResponsiveContainer>

      <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <div className="h-2 w-2 rounded-full bg-blue-500" />
            <span>Quality Score</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>7-Day Average</span>
          </div>
        </div>
        <div className="flex items-center space-x-1">
          <Calendar className="h-3 w-3" />
          <span>Last {rangeLabel}</span>
        </div>
      </div>
    </div>
  );
};

export default QualityChart;
