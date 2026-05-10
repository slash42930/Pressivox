import { useCallback, useState } from 'react'

type AsyncActionOptions<T> = {
  pendingStatus?: string
  successStatus?: string | ((result: T) => string)
  errorStatus?: string
  getErrorMessage?: (error: unknown) => string
  onSuccess?: (result: T) => void
  onError?: (message: string, error: unknown) => void
}

function defaultErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message
  }
  return 'Something went wrong. Please try again.'
}

export function useAsyncAction() {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  const runAction = useCallback(async <T,>(
    action: () => Promise<T>,
    options: AsyncActionOptions<T> = {},
  ): Promise<T | null> => {
    setLoading(true)
    setErrorMsg('')
    setStatus(options.pendingStatus ?? '')

    try {
      const result = await action()
      options.onSuccess?.(result)

      if (typeof options.successStatus === 'function') {
        setStatus(options.successStatus(result))
      } else if (typeof options.successStatus === 'string') {
        setStatus(options.successStatus)
      }

      return result
    } catch (error) {
      const message = options.getErrorMessage?.(error) ?? defaultErrorMessage(error)
      setErrorMsg(message)
      setStatus(options.errorStatus ?? '')
      options.onError?.(message, error)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  return {
    loading,
    status,
    errorMsg,
    runAction,
    setStatus,
    setErrorMsg,
  }
}
