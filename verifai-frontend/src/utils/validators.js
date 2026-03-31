export const isPositiveNumber = (value) => {
  return typeof value === 'number' && !Number.isNaN(value) && value >= 0;
};

export const isValidPercentage = (value) => {
  return typeof value === 'number' && value >= 0 && value <= 100;
};
