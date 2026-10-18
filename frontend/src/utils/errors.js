export function extractErrorMessage(err, fallback = 'Something went wrong') {
  if (!err) return fallback
  if (typeof err === 'string') return err

  if (Array.isArray(err.messages) && err.messages.length) {
    return err.messages[0]
  }

  if (err._server_messages) {
    try {
      const outer = JSON.parse(err._server_messages)
      if (Array.isArray(outer) && outer.length) {
        const inner = JSON.parse(outer[0])
        if (inner.message) return inner.message
      }
    } catch (e) {
      // fall through
    }
  }

  const msg = err.message || ''
  const isGeneric = /^\S+\s+\w+Error$/.test(msg) || /^(Validation|Permission|DoesNotExist|Authentication)Error$/.test(msg)
  if (msg && !isGeneric) return msg

  if (err.exception && typeof err.exception === 'string') {
    const cleaned = err.exception.replace(/^frappe\.exceptions\./, '')
    if (cleaned) return cleaned
  }

  return fallback
}