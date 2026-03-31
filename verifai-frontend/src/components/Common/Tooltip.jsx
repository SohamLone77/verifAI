import React from 'react';

const Tooltip = ({ text, children }) => {
  return (
    <span className="group relative inline-flex">
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 mb-2 hidden -translate-x-1/2 rounded bg-gray-900 px-2 py-1 text-xs text-white group-hover:block">
        {text}
      </span>
    </span>
  );
};

export default Tooltip;
