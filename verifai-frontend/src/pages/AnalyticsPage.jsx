import React, { useEffect, useState } from 'react';
import {
  TrendingUp,
  DollarSign,
  Star,
  Activity,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { useDashboardData, useDashboardStream } from '../hooks/useAnalytics';
import MetricCard from '../components/Dashboard/MetricCard';
import QualityChart from '../components/Dashboard/QualityChart';
import CostBreakdownChart from '../components/Dashboard/CostBreakdownChart';
import SavingsBreakdown from '../components/Dashboard/SavingsBreakdown';
import RecentActivity from '../components/Dashboard/RecentActivity';
import AlertsPanel from '../components/Dashboard/AlertsPanel';
import LoadingSpinner from '../components/Common/LoadingSpinner';

const AnalyticsPage = () => {
  const timeRanges = [
    { label: '7D', value: 7 },
    { label: '30D', value: 30 },
    { label: '90D', value: 90 },
  ];
  const [selectedDays, setSelectedDays] = useState(30);
  const [nowTick, setNowTick] = useState(Date.now());
  const streamStatus = useDashboardStream(selectedDays);
  const shouldPoll = streamStatus !== 'live';
  const {
    data,
    isLoading,
    error,
    refetch,
    isFetching,
  } = useDashboardData(selectedDays, {
    refetchInterval: shouldPoll ? 15000 : false,
  });

  const summary = data?.summary || {
    totalReviews: 0,
    averageScore: 0,
    totalCost: 0,
    roi: 0,
    trends: { reviews: 0, score: 0, cost: 0, roi: 0 },
  };

  const qualityData = data?.qualityData || [];
  const costData = data?.costData || { byModel: [], byAgent: [], byTask: [] };
  const savingsData = data?.savingsData || [];
  const recentActivity = data?.recentActivity || [];
  const alerts = data?.alerts || [];

  useEffect(() => {
    const timer = setInterval(() => setNowTick(Date.now()), 5000);
    return () => clearInterval(timer);
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <p className="text-red-500">Failed to load analytics data</p>
          <button className="mt-2 rounded-lg bg-blue-500 px-4 py-2 text-white">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Analytics</h1>
          <p className="text-sm text-gray-500">Performance and cost insights</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex rounded-lg border border-gray-200 bg-white shadow-sm">
            {timeRanges.map((range) => (
              <button
                key={range.value}
                onClick={() => setSelectedDays(range.value)}
                className={`px-3 py-1.5 text-sm transition-colors ${
                  selectedDays === range.value
                    ? 'bg-gray-100 text-gray-800'
                    : 'bg-white text-gray-600 hover:bg-gray-50'
                } ${range.value === 90 ? 'rounded-r-lg' : ''} ${
                  range.value === 7 ? 'rounded-l-lg' : ''
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center space-x-2 rounded-lg bg-white px-4 py-2 shadow-sm hover:bg-gray-50"
          >
            <RefreshCw className={`h-4 w-4 text-gray-500 ${isFetching ? 'animate-spin' : ''}`} />
            <span className="text-sm">{isFetching ? 'Refreshing' : 'Refresh'}</span>
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
        <span
          className={`h-2 w-2 rounded-full ${
            streamStatus === 'live'
              ? 'bg-green-500'
              : streamStatus === 'open'
              ? 'bg-blue-500'
              : streamStatus === 'error'
              ? 'bg-red-500'
              : 'bg-gray-400'
          }`}
        />
        <span>
          Live updates:{' '}
          {streamStatus === 'reconnecting'
            ? 'reconnecting...'
            : streamStatus}
        </span>
        {data?.lastUpdated && (
          <span className="flex items-center space-x-1">
            <Clock className="h-3 w-3" />
            <span>
              Last updated: {(() => {
                const diffMs = nowTick - new Date(data.lastUpdated).getTime();
                if (Number.isNaN(diffMs)) return 'unknown';
                const seconds = Math.max(0, Math.floor(diffMs / 1000));
                if (seconds < 5) return 'just now';
                if (seconds < 60) return `${seconds}s ago`;
                const minutes = Math.floor(seconds / 60);
                if (minutes < 60) return `${minutes}m ago`;
                const hours = Math.floor(minutes / 60);
                return `${hours}h ago`;
              })()}
            </span>
          </span>
        )}
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Reviews"
          value={summary.totalReviews}
          subtitle={`Last ${selectedDays} days`}
          trend={summary.trends.reviews}
          icon={Activity}
          color="blue"
        />
        <MetricCard
          title="Quality Score"
          value={summary.averageScore}
          subtitle={`Avg (last ${selectedDays} days)`}
          trend={summary.trends.score}
          icon={Star}
          color="green"
        />
        <MetricCard
          title="Total Cost"
          value={summary.totalCost}
          subtitle={`Last ${selectedDays} days`}
          trend={summary.trends.cost}
          icon={DollarSign}
          color="orange"
        />
        <MetricCard
          title="ROI"
          value={`${summary.roi}%`}
          subtitle="Annual return"
          trend={summary.trends.roi}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <QualityChart data={qualityData} rangeLabel={`${selectedDays}D`} />
        <CostBreakdownChart costData={costData} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SavingsBreakdown savingsData={savingsData} />
        <div className="space-y-6">
          <RecentActivity activities={recentActivity} />
          <AlertsPanel alerts={alerts} />
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
