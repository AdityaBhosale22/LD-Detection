import { useCallback, useEffect, useState } from 'react'

/** Load data on mount; exposes `reload` for refreshing after an action. */
export function useLoad<T>(loader: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(() => {
    setLoading(true)
    setError(null)
    return loader()
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [loader])

  useEffect(() => {
    reload()
  }, [reload])

  return { data, error, loading, reload }
}
