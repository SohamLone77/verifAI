import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { NumericFormat } from 'react-number-format';

const MetricCard = ({ title, value, subtitle, trend, icon: Icon, color = 'blue' }) => {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-emerald-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
    red: 'from-red-500 to-red-600',
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    if (trend > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
      className="overflow-hidden rounded-xl bg-white shadow-lg"
    >
      <div className={`h-1 bg-gradient-to-r ${colors[color]}`} />
      <div className="p-5">
        <div className="flex items-center justify-between">
          <div className="rounded-lg bg-gray-50 p-2">
            {Icon && <Icon className={`h-5 w-5 text-${color}-500`} />}
          </div>
          {trend !== undefined && (
            <div className="flex items-center space-x-1 rounded-full bg-gray-50 px-2 py-1">
              {getTrendIcon()}
              <span
                className={`text-xs font-medium ${
                  trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
                }`}
              >
                {Math.abs(trend)}%
              </span>
            </div>
          )}
        </div>

        <div className="mt-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-1 text-2xl font-bold text-gray-800">
            {typeof value === 'number' ? (
              <NumericFormat
                value={value}
                displayType="text"
                thousandSeparator={true}
                prefix={title.includes('Cost') || title.includes('Savings') ? '$' : ''}
                decimalScale={title.includes('Score') ? 2 : 0}
                renderText={(formatted) => formatted}
              />
            ) : (
              value
            )}
          </p>
          {subtitle && <p className="mt-1 text-xs text-gray-500">{subtitle}</p>}
        </div>
      </div>
    </motion.div>
  );
};

export default MetricCard;
