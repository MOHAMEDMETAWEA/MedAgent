import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook acting as the Controller in the MVC pattern.
 * It manages the lifecycle, state, and business logic of data fetching,
 * keeping the View (React component) clean and focused strictly on the UI.
 * 
 * @param {Function} fetcher - The service function to call (e.g., MockService.getPrescriptions)
 */
export const useHealthData = (fetcher) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await fetcher();
      setData(result);
    } catch (err) {
      setError(err);
      console.error("Controller Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, refetch: execute };
};
