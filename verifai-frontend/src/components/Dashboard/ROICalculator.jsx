import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Calculator, TrendingUp, DollarSign, Clock, Award } from 'lucide-react';
import { NumericFormat } from 'react-number-format';
import toast from 'react-hot-toast';

const ROICalculator = () => {
  const [inputs, setInputs] = useState({
    dailyVolume: 5000,
    costPerReview: 0.05,
    manualReviewCost: 0.5,
    errorRate: 0.15,
    errorReduction: 0.95,
    costPerIncident: 5000,
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const calculateROI = async () => {
    setLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const annualVolume = inputs.dailyVolume * 365;
      const manualCost = annualVolume * inputs.manualReviewCost;
      const verifaiCost = annualVolume * inputs.costPerReview;
      const laborSavings = manualCost - verifaiCost;

      const errorCostWithout = annualVolume * inputs.errorRate * inputs.costPerIncident;
      const errorCostWith = errorCostWithout * (1 - inputs.errorReduction);
      const errorSavings = errorCostWithout - errorCostWith;

      const totalSavings = laborSavings + errorSavings;
      const netProfit = totalSavings - verifaiCost;
      const roi = (netProfit / verifaiCost) * 100;
      const paybackDays = verifaiCost / (totalSavings / 365);

      setResults({
        laborSavings,
        errorSavings,
        totalSavings,
        verifaiCost,
        netProfit,
        roi,
        paybackDays,
      });

      toast.success('ROI calculation complete!');
    } catch (error) {
      toast.error('Failed to calculate ROI');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setInputs((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-xl bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-center space-x-2">
          <Calculator className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-semibold text-gray-800">ROI Parameters</h3>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Daily Review Volume
            </label>
            <NumericFormat
              value={inputs.dailyVolume}
              onValueChange={(values) => handleInputChange('dailyVolume', values.floatValue)}
              thousandSeparator={true}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              VerifAI Cost per Review ($)
            </label>
            <input
              type="number"
              step="0.01"
              value={inputs.costPerReview}
              onChange={(e) => handleInputChange('costPerReview', parseFloat(e.target.value))}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Current Error Rate (%)
            </label>
            <input
              type="number"
              step="0.01"
              value={inputs.errorRate * 100}
              onChange={(e) => handleInputChange('errorRate', parseFloat(e.target.value) / 100)}
              className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            onClick={calculateROI}
            disabled={loading}
            className="w-full rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 py-2.5 font-medium text-white transition-all hover:from-blue-600 hover:to-blue-700 disabled:opacity-50"
          >
            {loading ? 'Calculating...' : 'Calculate ROI'}
          </button>
        </div>
      </div>

      {results && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="rounded-xl bg-gradient-to-br from-green-50 to-emerald-50 p-6 shadow-lg"
        >
          <div className="mb-4 flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <h3 className="text-lg font-semibold text-gray-800">ROI Results</h3>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg bg-white p-3">
                <div className="flex items-center space-x-1 text-sm text-gray-500">
                  <DollarSign className="h-4 w-4" />
                  <span>Annual Savings</span>
                </div>
                <p className="text-xl font-bold text-green-600">
                  ${(results.totalSavings / 1000).toFixed(0)}K
                </p>
              </div>

              <div className="rounded-lg bg-white p-3">
                <div className="flex items-center space-x-1 text-sm text-gray-500">
                  <Clock className="h-4 w-4" />
                  <span>Payback Period</span>
                </div>
                <p className="text-xl font-bold text-blue-600">
                  {Math.round(results.paybackDays)} days
                </p>
              </div>
            </div>

            <div className="rounded-lg bg-white p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">ROI</span>
                <span className="text-3xl font-bold text-green-600">
                  {Math.round(results.roi)}%
                </span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-gray-200">
                <div
                  className="h-2 rounded-full bg-gradient-to-r from-green-500 to-emerald-500"
                  style={{ width: `${Math.min(results.roi / 10, 100)}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Labor Savings</p>
                <p className="font-semibold">${(results.laborSavings / 1000).toFixed(0)}K</p>
              </div>
              <div>
                <p className="text-gray-500">Error Savings</p>
                <p className="font-semibold">${(results.errorSavings / 1000).toFixed(0)}K</p>
              </div>
            </div>

            <div className="flex items-center justify-between rounded-lg bg-white p-3">
              <div className="flex items-center space-x-2">
                <Award className="h-4 w-4 text-yellow-500" />
                <span className="text-sm font-medium">Recommendation</span>
              </div>
              <span className="text-sm text-green-600">
                {results.roi > 200 ? 'Strong Buy' : results.roi > 100 ? 'Buy' : 'Consider'}
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ROICalculator;
