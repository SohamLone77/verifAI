import { useEffect, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { analyticsAPI } from '../services/api';

const apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const analyticsApiKey = process.env.REACT_APP_ANALYTICS_API_KEY;

export const useDashboardData = (days = 30, options = {}) => {
  const baseOptions = {
    staleTime: 5000,
    cacheTime: 30000,
    refetchInterval: 15000,
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  };

  return useQuery(['dashboard', days], () => analyticsAPI.getDashboardData(days), {
    ...baseOptions,
    ...options,
  });
};

export const useDashboardStream = (days = 30, interval = 5) => {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState('connecting');
  const retryRef = useRef(0);
  const timeoutRef = useRef(null);
  const sourceRef = useRef(null);

  const scheduleReconnect = () => {
    const attempt = retryRef.current;
    const baseDelay = Math.min(30000, 1000 * 2 ** attempt);
    const jitter = Math.floor(Math.random() * 500);
    retryRef.current += 1;
    timeoutRef.current = setTimeout(() => {
      connect();
    }, baseDelay + jitter);
  };

  const connect = () => {
    const streamUrl = new URL('/analytics/stream', apiBaseUrl);
    streamUrl.searchParams.set('days', String(days));
    streamUrl.searchParams.set('interval', String(interval));
    if (analyticsApiKey) {
      streamUrl.searchParams.set('api_key', analyticsApiKey);
    }
    const source = new EventSource(streamUrl.toString());
    sourceRef.current = source;

    source.onopen = () => {
      retryRef.current = 0;
      setStatus('open');
    };

    source.onerror = () => {
      setStatus('reconnecting');
      source.close();
      scheduleReconnect();
    };

    source.addEventListener('ping', () => {
      setStatus((prev) => (prev === 'live' ? prev : 'open'));
    });

    source.onmessage = (event) => {
      if (!event.data) return;
      try {
        const payload = JSON.parse(event.data);
        queryClient.setQueryData(['dashboard', days], payload);
        setStatus('live');
      } catch (error) {
        setStatus('error');
      }
    };
  };

  useEffect(() => {
    setStatus('connecting');
    connect();

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (sourceRef.current) {
        sourceRef.current.close();
      }
    };
  }, [days, interval, queryClient]);

  return status;
};

export const useROI = () => {
  const queryClient = useQueryClient();

  return useMutation((params) => analyticsAPI.getROI(params), {
    onSuccess: (data) => {
      queryClient.setQueryData(['roi', data.inputs], data);
    },
  });
};

export const useQualityMetrics = (days = 30) => {
  return useQuery(['quality', days], () => analyticsAPI.getQualityMetrics(days), {
    staleTime: 60000,
  });
};

export const useCostBreakdown = (days = 30) => {
  return useQuery(['cost', days], () => analyticsAPI.getCostBreakdown(days), {
    staleTime: 60000,
  });
};

export const useBenchmarks = (industry) => {
  return useQuery(['benchmarks', industry], () => analyticsAPI.getBenchmarks(industry), {
    enabled: !!industry,
    staleTime: 3600000,
  });
};
