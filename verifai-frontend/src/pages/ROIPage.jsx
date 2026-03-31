import React from 'react';
import ROICalculator from '../components/Dashboard/ROICalculator';

const ROIPage = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-800">ROI Calculator</h1>
        <p className="text-sm text-gray-500">Estimate financial impact with VerifAI</p>
      </div>
      <ROICalculator />
    </div>
  );
};

export default ROIPage;
