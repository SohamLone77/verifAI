import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="flex items-center space-x-3">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500" />
      <span className="text-sm text-gray-500">Loading...</span>
    </div>
  );
};

export default LoadingSpinner;
